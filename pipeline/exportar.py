"""3ª conferência e exportação: gera web/dados.json (e web/dados.js de reserva, para abrir com duplo clique, offline)
a partir das views de indicadores e da malha simplificada no PostGIS. Para o processo se algum total não bater.
Uso: python pipeline/exportar.py"""
import json
import sys
from banco import RAIZ, TOTAL_CASOS, TOTAL_MUNICIPIOS, TOTAL_MULHERES, ANOS, TIPOS, Falha, confere, consulta

WEB = RAIZ / "web"
FAIXAS = ["<1 Ano", "1-4", "5-9", "10-14", "15-19", "20-29", "30-39", "40-49", "50-59", "60 e mais", "Ign/Branco"]
TOLERANCIA_SIMPLIFICACAO = 0.001   # graus (cerca de 100 m): reduz o arquivo sem mudar o desenho do mapa
CASAS_COORD = 3


def main():
    muns = consulta(f"""SELECT m.cod_ibge7, m.nome, p.pop_fem_2022,
        ST_AsGeoJSON(ST_SimplifyPreserveTopology(m.geom, {TOLERANCIA_SIMPLIFICACAO}), {CASAS_COORD}) AS geom
        FROM websig.municipio m JOIN websig.populacao p USING (cod_ibge7) ORDER BY m.cod_ibge7""")
    ind = consulta("""SELECT cod_ibge7, ano, tipo, casos, taxa_100mil_ano, o_sobre_e
        FROM websig.vw_indicador_municipio_ano_tipo ORDER BY cod_ibge7, tipo, ano NULLS LAST""")
    reg = {r["cod_ibge7"]: r for r in consulta("""SELECT m.cod_ibge7, r.cod_regiao, r.regiao, r.cod_macro, r.macrorregiao
        FROM websig.regiao_saude r JOIN websig.municipio m USING (cod_ibge6)""")}
    taxa_reg = {(r["cod_regiao"], r["tipo"]): float(r["taxa_100mil_ano"]) for r in consulta(
        "SELECT cod_regiao, tipo, taxa_100mil_ano FROM websig.vw_indicador_regiao WHERE periodo = '2019-2024'")}
    popfx = consulta("SELECT cod_ibge7, faixa_id, mulheres FROM websig.populacao_faixa ORDER BY cod_ibge7, faixa_id")
    taxa_fx = {(r["cod_ibge7"], int(r["faixa_id"])): float(r["taxa_100mil_ano"]) for r in consulta(
        "SELECT cod_ibge7, faixa_id, taxa_100mil_ano FROM websig.vw_faixa_municipio WHERE taxa_100mil_ano IS NOT NULL")}
    rede = {r["cod_ibge7"]: r for r in consulta("SELECT * FROM websig.rede_atendimento")}
    local = {}   # cod -> [mesma região de saúde, outra região da PB, fora da Paraíba]
    pct_local = {}
    for r in consulta("SELECT cod_ibge7, categoria, casos, pct FROM websig.vw_local_atendimento"):
        local.setdefault(r["cod_ibge7"], [0, 0, 0])[int(r["categoria"]) - 1] = int(r["casos"])
        pct_local[(r["cod_ibge7"], int(r["categoria"]))] = float(r["pct"]) if r["pct"] not in ("", None) else None
    fx = consulta("""SELECT m.cod_ibge7, f.faixa_id, f.casos FROM websig.faixa_etaria f
        JOIN websig.municipio m USING (cod_ibge6) ORDER BY m.cod_ibge7, f.faixa_id""")

    casos = {}      # cod -> tipo -> [casos por ano]
    acum = {}       # (cod, tipo) -> (casos, taxa, o/e) do acumulado, para a conferência do cálculo
    for r in ind:
        if r["ano"]:
            casos.setdefault(r["cod_ibge7"], {t: [0] * len(ANOS) for t in TIPOS})[r["tipo"]][ANOS.index(int(r["ano"]))] = int(r["casos"])
        else:
            acum[(r["cod_ibge7"], r["tipo"])] = (int(r["casos"]), float(r["taxa_100mil_ano"]), float(r["o_sobre_e"]))
    faixa = {}
    for r in fx:
        faixa.setdefault(r["cod_ibge7"], [0] * len(FAIXAS))[int(r["faixa_id"]) - 1] = int(r["casos"])

    mulheres_fx = {}   # cod -> [mulheres nas 10 faixas do SINAN, sem a "Ignorada"]
    for r in popfx:
        mulheres_fx.setdefault(r["cod_ibge7"], [0] * 10)[int(r["faixa_id"]) - 1] = int(r["mulheres"])
    feats = []
    for m in muns:
        c = m["cod_ibge7"]
        feats.append({"type": "Feature", "geometry": json.loads(m["geom"]),
                      "properties": {"cod": c, "nome": m["nome"], "pop": int(m["pop_fem_2022"]),
                                     "reg": reg[c]["cod_regiao"], "casos": casos[c], "faixa": faixa[c], "popfx": mulheres_fx[c], "local": local[c],
                                     # MUNIC 2023, exatamente como declarado: "Sim", "Não" ou "-" (sem dado)
                                     "rede": {k: rede[c][k] for k in ("organismo_politicas_mulheres", "centro_referencia", "casa_abrigo", "delegacia_mulher")}}})
    regioes = {r["cod_regiao"]: {"nome": r["regiao"], "macro": r["macrorregiao"], "cod_macro": r["cod_macro"]}
               for r in sorted(reg.values(), key=lambda r: r["cod_regiao"])}

    # Conferências da exportação
    pop = sum(f["properties"]["pop"] for f in feats)
    tot = sum(sum(f["properties"]["casos"]["total"]) for f in feats)
    tot_fx = sum(sum(f["properties"]["faixa"]) for f in feats)
    confere(len(feats) == TOTAL_MUNICIPIOS, f"{len(feats)} municípios (esperado {TOTAL_MUNICIPIOS})")
    confere(pop == TOTAL_MULHERES, f"{pop} mulheres (esperado {TOTAL_MULHERES})")
    confere(tot == TOTAL_CASOS, f"{tot} casos (esperado {TOTAL_CASOS})")
    confere(tot_fx == TOTAL_CASOS, f"faixa etária soma {tot_fx} (esperado {TOTAL_CASOS})")
    confere(len(regioes) == 16 and len({r["cod_macro"] for r in regioes.values()}) == 3, f"{len(regioes)} regiões de saúde (esperado 16)")
    # Taxa da região (média da região na ficha) recalculada do arquivo = view
    for (cr, t), v in taxa_reg.items():
        ps = [f["properties"] for f in feats if f["properties"]["reg"] == cr]
        tx = sum(sum(p["casos"][t]) for p in ps) / sum(p["pop"] for p in ps) * 100000 / len(ANOS)
        confere(abs(tx - v) < 1e-6, f"taxa da região {cr} ({t}) diverge da view")
    # Mulheres por faixa: soma = total de cada município; taxa por faixa recalculada do arquivo = view
    for f in feats:
        p = f["properties"]
        confere(sum(p["popfx"]) == p["pop"], f"mulheres por faixa não somam o total em {p['nome']}")
        for i in range(10):
            tx = p["faixa"][i] / p["popfx"][i] * 100000 / len(ANOS)
            confere(abs(tx - taxa_fx[(p["cod"], i + 1)]) < 1e-6, f"taxa da faixa {FAIXAS[i]} diverge da view em {p['nome']}")
    confere(sum(sum(f["properties"]["popfx"]) for f in feats) == TOTAL_MULHERES, "mulheres por faixa: total do estado")
    confere(len(rede) == TOTAL_MUNICIPIOS, f"rede de atendimento: {len(rede)} municípios")
    # Local de notificação: as três categorias somam os casos por residência; % recalculado do arquivo = view
    for f in feats:
        p = f["properties"]; tot_p = sum(p["casos"]["total"])
        confere(sum(p["local"]) == tot_p, f"local de notificação não soma os casos em {p['nome']}")
        for k in range(3):
            v = pct_local[(p["cod"], k + 1)]
            confere((v is None and tot_p == 0) or (tot_p and abs(p["local"][k] * 100 / tot_p - v) < 1e-6), f"% do local de notificação diverge da view em {p['nome']}")
    confere(sum(sum(f["properties"]["local"]) for f in feats) == TOTAL_CASOS, "local de notificação: total do estado")
    # As fórmulas do painel aplicadas ao arquivo exportado têm de reproduzir a view (acumulado 2019-2024)
    for t in TIPOS:
        est = sum(sum(f["properties"]["casos"][t]) for f in feats)
        for f in feats:
            p = f["properties"]
            cs = sum(p["casos"][t])
            taxa = cs / p["pop"] * 100000 / len(ANOS)
            oe = cs / (p["pop"] * est / pop)
            v_casos, v_taxa, v_oe = acum[(p["cod"], t)]
            confere(cs == v_casos and abs(taxa - v_taxa) < 1e-6 and abs(oe - v_oe) < 1e-6,
                    f"cálculo diverge da view em {p['nome']} ({t})")

    dados = {"type": "FeatureCollection", "features": feats, "anos": ANOS, "faixas": FAIXAS, "regioes": regioes,
             "fonte": "SINAN/TABNET (notificações de mulheres, município de residência, sem violência autoprovocada) e IBGE Censo 2022",
             "fonte_regioes": "Ministério da Saúde/DATASUS, Base Territorial (jun/2026): região e macrorregião de saúde",
             "fonte_faixas": "IBGE, Censo 2022, SIDRA 9514: mulheres por idade, somadas nas faixas do SINAN",
             "fonte_rede": "IBGE, MUNIC 2023: serviços declarados pela prefeitura",
             "fonte_local": "SINAN/TABNET: município de residência × região de saúde de notificação; fora da PB = casos por residência − notificados na PB"}
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    (WEB / "dados.json").write_text(texto, encoding="utf-8")
    (WEB / "dados.js").write_text("window.DADOS=" + texto + ";\n", encoding="utf-8")
    print(f"Exportação OK: {len(feats)} municípios, {tot} casos, {pop} mulheres; dados.json com {len(texto.encode()) // 1024} KB")


if __name__ == "__main__":
    try:
        main()
    except Falha as e:
        print(f"ERRO na exportação: {e}")
        sys.exit(1)
