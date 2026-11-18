"""1ª conferência: os dados brutos (antes da carga). Para o processo se algum total não bater.
Uso: python pipeline/conferir.py"""
import csv
import json
import sys
from banco import RAIZ, TOTAL_CASOS, TOTAL_MUNICIPIOS, TOTAL_MULHERES, ANOS, Falha, confere

BRUTOS = RAIZ / "dados" / "brutos"
TIPOS_SINAN = ["total_sem_autoprovocada", "fisica", "psicologica_moral", "sexual"]


def ler(nome):
    with open(BRUTOS / nome, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    pop = ler("ibge_populacao_feminina_2022.csv")
    cods7 = {r["cod_ibge7"] for r in pop}
    cods6 = {r["cod_ibge6"] for r in pop}
    confere(len(pop) == TOTAL_MUNICIPIOS and len(cods7) == TOTAL_MUNICIPIOS, f"população: {len(pop)} linhas, {len(cods7)} códigos")
    confere(all(r["cod_ibge6"] == r["cod_ibge7"][:6] for r in pop), "código de 6 dígitos diferente do início do de 7")
    soma_pop = sum(int(r["pop_fem_2022"]) for r in pop)
    confere(soma_pop == TOTAL_MULHERES, f"mulheres = {soma_pop} (esperado {TOTAL_MULHERES})")

    malha = json.loads((BRUTOS / "malha_municipal_pb_geojs.json").read_text(encoding="utf-8"))
    cods_malha = {f["properties"]["id"] for f in malha["features"]}
    confere(cods_malha == cods7, f"malha e população com códigos diferentes: {sorted(cods_malha ^ cods7)[:5]}")

    sinan = ler("sinan_pb_mulheres_residencia_2019-2024_longo.csv")
    usados = [r for r in sinan if r["tipo"] in TIPOS_SINAN]
    ignorado = sum(int(r["casos"]) for r in usados if r["cod_ibge6"] == "000000")
    confere(ignorado == 0, f"{ignorado} casos em 'município ignorado'")
    cods_sinan = {r["cod_ibge6"] for r in usados} - {"000000"}
    confere(cods_sinan == cods6, f"SINAN e população com códigos diferentes: {sorted(cods_sinan ^ cods6)[:5]}")
    total = sum(int(r["casos"]) for r in usados if r["tipo"] == "total_sem_autoprovocada")
    confere(total == TOTAL_CASOS, f"casos = {total} (esperado {TOTAL_CASOS})")
    serie = [sum(int(r["casos"]) for r in usados if r["tipo"] == "total_sem_autoprovocada" and int(r["ano"]) == a) for a in ANOS]

    fx = ler("sinan_pb_mulheres_residencia_faixa_etaria_2019-2024.csv")
    soma_fx = sum(int(r["casos"]) for r in fx)
    confere(soma_fx == TOTAL_CASOS, f"faixa etária soma {soma_fx} (esperado {TOTAL_CASOS})")
    confere({r["cod_ibge6"] for r in fx} <= cods6, "faixa etária com município desconhecido")

    # Região de saúde (DATASUS, Base Territorial): todo município da PB em exatamente uma região
    terr = BRUTOS / "datasus_base_territorial_jun26"
    with open(terr / "rl_municip_regsaud.csv", encoding="utf-8") as f:
        mun_reg = [r for r in csv.DictReader(f, delimiter=";") if r["CO_MUNICIP"] in cods6]
    regs = {r["CO_REGSAUD"] for r in mun_reg}
    confere(len(mun_reg) == TOTAL_MUNICIPIOS and {r["CO_MUNICIP"] for r in mun_reg} == cods6, f"região de saúde: {len(mun_reg)} municípios (esperado {TOTAL_MUNICIPIOS})")
    confere(len(regs) == 16, f"{len(regs)} regiões de saúde na PB (esperado 16)")

    print(f"Dados brutos OK: {len(pop)} municípios, {total} casos, {soma_pop} mulheres, {len(regs)} regiões de saúde; série anual {serie}")


if __name__ == "__main__":
    try:
        main()
    except (Falha, FileNotFoundError) as e:
        print(f"ERRO na conferência dos dados brutos: {e}")
        sys.exit(1)
