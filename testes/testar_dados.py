"""Teste dos dados: totais, somas por tipo e por faixa etária, banco × dados brutos × dados.json/dados.js.
Uso: python testes/testar_dados.py   (precisa do banco carregado e da exportação feita)"""
import csv
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pipeline"))
from banco import RAIZ, TOTAL_CASOS, TOTAL_MUNICIPIOS, TOTAL_MULHERES, ANOS, TIPOS, consulta  # noqa: E402

BRUTOS = RAIZ / "dados" / "brutos"
MAPA_TIPO = {"total_sem_autoprovocada": "total", "fisica": "fisica", "psicologica_moral": "psicologica", "sexual": "sexual"}
FAIXAS = ["<1 Ano", "1-4", "5-9", "10-14", "15-19", "20-29", "30-39", "40-49", "50-59", "60 e mais", "Ign/Branco"]
falhas, ok = [], []


def check(cond, msg):
    (ok if cond else falhas).append(msg)


def ler(nome):
    with open(BRUTOS / nome, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ---------- dados brutos (referência) ----------
sinan = [r for r in ler("sinan_pb_mulheres_residencia_2019-2024_longo.csv") if r["tipo"] in MAPA_TIPO and r["cod_ibge6"] != "000000"]
bruto_tipo = {MAPA_TIPO[t]: sum(int(r["casos"]) for r in sinan if r["tipo"] == t) for t in MAPA_TIPO}
bruto_ano = {(MAPA_TIPO[r["tipo"]], int(r["ano"])): 0 for r in sinan}
for r in sinan:
    bruto_ano[(MAPA_TIPO[r["tipo"]], int(r["ano"]))] += int(r["casos"])
fx_bruto = ler("sinan_pb_mulheres_residencia_faixa_etaria_2019-2024.csv")
bruto_faixa = {f: sum(int(r["casos"]) for r in fx_bruto if r["faixa_etaria"] == f) for f in FAIXAS}
pop_bruto = {r["cod_ibge7"]: (r["nome_oficial"], int(r["pop_fem_2022"])) for r in ler("ibge_populacao_feminina_2022.csv")}

# ---------- banco ----------
tot = consulta("SELECT (SELECT count(*) FROM websig.municipio) AS mun, (SELECT sum(pop_fem_2022) FROM websig.populacao) AS pop, "
               "(SELECT sum(casos) FROM websig.notificacao WHERE tipo='total') AS casos, (SELECT sum(casos) FROM websig.faixa_etaria) AS faixa")[0]
check(int(tot["mun"]) == TOTAL_MUNICIPIOS, f"banco: {tot['mun']} municípios (esperado {TOTAL_MUNICIPIOS})")
check(int(tot["pop"]) == TOTAL_MULHERES, f"banco: {tot['pop']} mulheres (esperado {TOTAL_MULHERES})")
check(int(tot["casos"]) == TOTAL_CASOS, f"banco: {tot['casos']} casos (esperado {TOTAL_CASOS})")
check(int(tot["faixa"]) == TOTAL_CASOS, f"banco: faixa etária soma {tot['faixa']} (esperado {TOTAL_CASOS})")
for r in consulta("SELECT tipo, sum(casos) AS c FROM websig.notificacao GROUP BY tipo"):
    check(int(r["c"]) == bruto_tipo[r["tipo"]], f"banco: tipo {r['tipo']} = {r['c']} (bruto {bruto_tipo[r['tipo']]})")
for r in consulta("SELECT tipo, ano, casos FROM websig.vw_indicador_estado WHERE ano IS NOT NULL"):
    check(int(r["casos"]) == bruto_ano[(r["tipo"], int(r["ano"]))], f"view estado: {r['tipo']} {r['ano']} = {r['casos']}")
serie = [int(r["casos"]) for r in consulta("SELECT casos FROM websig.vw_indicador_estado WHERE tipo='total' AND ano IS NOT NULL ORDER BY ano")]
check(serie == [1740, 1256, 1360, 1700, 1953, 2335], f"série anual {serie}")
for r in consulta("SELECT faixa, sum(casos) AS c FROM websig.faixa_etaria GROUP BY faixa"):
    check(int(r["c"]) == bruto_faixa[r["faixa"]], f"banco: faixa {r['faixa']} = {r['c']} (bruto {bruto_faixa[r['faixa']]})")
div = consulta("SELECT count(*) AS n FROM (SELECT f.cod_ibge6 FROM websig.faixa_etaria f GROUP BY f.cod_ibge6 "
               "HAVING sum(f.casos) <> (SELECT sum(casos) FROM websig.notificacao n WHERE n.cod_ibge6=f.cod_ibge6 AND n.tipo='total')) x")[0]["n"]
check(int(div) == 0, f"faixa etária × total por município: {div} divergências")
# Fórmulas das views conferidas linha a linha (estado e municípios)
est = {(r["periodo"], r["tipo"]): r for r in consulta("SELECT * FROM websig.vw_indicador_estado")}
erro_view = 0
for r in consulta("SELECT * FROM websig.vw_indicador_municipio_ano_tipo"):
    e = est[(r["periodo"], r["tipo"])]
    c, p, n = int(r["casos"]), int(r["pop_fem_2022"]), int(r["n_anos"])
    esp = p * int(e["casos"]) / int(e["pop_fem_2022"])
    if abs(float(r["taxa_100mil_ano"]) - c / p * 100000 / n) > 1e-9 or abs(float(r["esperado"]) - esp) > 1e-9 or abs(float(r["o_sobre_e"]) - c / esp) > 1e-9:
        erro_view += 1
check(erro_view == 0, f"view municipal: {erro_view} linhas com fórmula divergente")
check(len(est) == len(TIPOS) * (len(ANOS) + 1), f"view estado: {len(est)} combinações período × tipo")

# ---------- dados.json e dados.js ----------
web = RAIZ / "web"
dj = json.loads((web / "dados.json").read_text(encoding="utf-8"))
js = (web / "dados.js").read_text(encoding="utf-8")
check(js.startswith("window.DADOS=") and json.loads(js[len("window.DADOS="):].rstrip().rstrip(";")) == dj, "dados.js igual ao dados.json")
feats = {f["properties"]["cod"]: f["properties"] for f in dj["features"]}
check(len(feats) == TOTAL_MUNICIPIOS, f"dados.json: {len(feats)} municípios")
check(sum(p["pop"] for p in feats.values()) == TOTAL_MULHERES, "dados.json: total de mulheres")
check(sum(sum(p["casos"]["total"]) for p in feats.values()) == TOTAL_CASOS, "dados.json: total de casos")
check(all(feats[c]["nome"] == pop_bruto[c][0] and feats[c]["pop"] == pop_bruto[c][1] for c in pop_bruto), "dados.json: nomes e mulheres iguais ao IBGE")
banco_casos = consulta("SELECT cod_ibge7, ano, tipo, casos FROM websig.vw_indicador_municipio_ano_tipo WHERE ano IS NOT NULL")
dif = [r for r in banco_casos if feats[r["cod_ibge7"]]["casos"][r["tipo"]][ANOS.index(int(r["ano"]))] != int(r["casos"])]
check(not dif, f"dados.json × banco (casos por município, ano e tipo): {len(dif)} diferenças em {len(banco_casos)}")
banco_fx = consulta("SELECT m.cod_ibge7, f.faixa_id, f.casos FROM websig.faixa_etaria f JOIN websig.municipio m USING (cod_ibge6)")
dif = [r for r in banco_fx if feats[r["cod_ibge7"]]["faixa"][int(r["faixa_id"]) - 1] != int(r["casos"])]
check(not dif, f"dados.json × banco (faixa etária): {len(dif)} diferenças")

# Região de saúde (DATASUS): 223 municípios em 16 regiões e 3 macrorregiões; a view da região soma o estado
rg = consulta("SELECT count(*) AS n, count(DISTINCT cod_regiao) AS r, count(DISTINCT cod_macro) AS m FROM websig.regiao_saude")[0]
check((int(rg["n"]), int(rg["r"]), int(rg["m"])) == (TOTAL_MUNICIPIOS, 16, 3), f"região de saúde: {rg['n']} municípios, {rg['r']} regiões, {rg['m']} macrorregiões")
somas = consulta("SELECT e.periodo, e.tipo, e.casos AS est, sum(g.casos) AS reg FROM websig.vw_indicador_estado e "
                 "JOIN websig.vw_indicador_regiao g USING (periodo, tipo) GROUP BY e.periodo, e.tipo, e.casos")
difs = [f"{r['periodo']} {r['tipo']}" for r in somas if int(r["est"]) != int(r["reg"])]
check(len(somas) == len(TIPOS) * (len(ANOS) + 1) and not difs, f"view da região: as 16 regiões somam o estado em cada período e tipo ({difs[:3]})")
check(all(p.get("reg") in dj.get("regioes", {}) for p in feats.values()) and len(dj.get("regioes", {})) == 16, "dados.json: todo município tem uma das 16 regiões de saúde")

# Mulheres por faixa etária (SIDRA 9514): 223 × 10 faixas; soma de cada município = total; estado = 2.055.832
pf = consulta("SELECT cod_ibge7, faixa_id, mulheres FROM websig.populacao_faixa")
soma_pf = {}
for r in pf:
    soma_pf[r["cod_ibge7"]] = soma_pf.get(r["cod_ibge7"], 0) + int(r["mulheres"])
check(len(pf) == TOTAL_MUNICIPIOS * 10 and len(soma_pf) == TOTAL_MUNICIPIOS, f"populacao_faixa: {len(pf)} linhas (esperado {TOTAL_MUNICIPIOS * 10})")
check(all(soma_pf[c] == pop_bruto[c][1] for c in pop_bruto), "populacao_faixa: soma das faixas = mulheres do município (IBGE), nos 223")
check(sum(soma_pf.values()) == TOTAL_MULHERES, f"populacao_faixa: estado soma {sum(soma_pf.values())} (esperado {TOTAL_MULHERES})")
# Taxa por faixa na view = casos ÷ mulheres × 100.000 ÷ 6; "Ignorada" sem taxa
vf = consulta("SELECT cod_ibge7, faixa_id, casos, mulheres, taxa_100mil_ano FROM websig.vw_faixa_municipio")
erro_fx = [r for r in vf if int(r["faixa_id"]) <= 10 and abs(float(r["taxa_100mil_ano"]) - int(r["casos"]) / int(r["mulheres"]) * 100000 / 6) > 1e-6]
ign_ok = all(r["taxa_100mil_ano"] in ("", None) for r in vf if int(r["faixa_id"]) == 11)
check(len(vf) == TOTAL_MUNICIPIOS * 11 and not erro_fx and ign_ok, f"vw_faixa_municipio: taxa por faixa = fórmula ({len(erro_fx)} divergências; Ignorada sem taxa: {ign_ok})")
# Rede de atendimento (MUNIC 2023) = arquivo bruto, valores exatamente como na MUNIC
rede_bruto = {r["cod_ibge7"]: r for r in ler("ibge_munic2023_rede_atendimento_pb.csv")}
rede = consulta("SELECT * FROM websig.rede_atendimento")
COLS_REDE = ["organismo_politicas_mulheres", "centro_referencia", "casa_abrigo", "delegacia_mulher"]
dif_rede = [r["cod_ibge7"] for r in rede if any(r[k] != rede_bruto[r["cod_ibge7"]][k] for k in COLS_REDE)]
check(len(rede) == TOTAL_MUNICIPIOS and not dif_rede and all(r[k] in ("Sim", "Não", "-") for r in rede for k in COLS_REDE),
      f"rede_atendimento: 223 municípios iguais à MUNIC 2023 ({len(dif_rede)} diferenças)")
check(all(feats[c]["popfx"] == [int(r["mulheres"]) for r in sorted((x for x in pf if x["cod_ibge7"] == c), key=lambda x: int(x["faixa_id"]))] for c in list(feats)[:223])
      and all(feats[c]["rede"] == {k: rede_bruto[c][k] for k in COLS_REDE} for c in feats), "dados.json: mulheres por faixa e rede MUNIC iguais ao banco")

print(f"Teste dos dados: {len(ok)} verificações OK, {len(falhas)} falhas")
for f in falhas:
    print("  FALHA:", f)
sys.exit(1 if falhas else 0)
