"""Extrai da MUNIC 2023 (IBGE) as respostas dos 223 municípios da Paraíba usadas como contexto no painel.
Entrada: Base_MUNIC_2023.xlsx (23 MB), baixada de ftp://ftp.ibge.gov.br/Perfil_Municipios/2023/Base_de_Dados/
Saída: dados/brutos/ibge_munic2023_rede_atendimento_pb.csv, com os valores EXATAMENTE como na MUNIC ("Sim", "Não", "-").
Uso (só quando sair uma nova versão da planilha): python pipeline/extrair_munic2023.py caminho/Base_MUNIC_2023.xlsx
Requer: pip install openpyxl (o restante do pipeline usa só a biblioteca padrão)."""
import csv
import sys

from banco import RAIZ, TOTAL_MUNICIPIOS, Falha, confere

# aba da MUNIC -> (variável, nome da coluna no CSV)
VARIAVEIS = {
    "Política para Mulheres": [("MPPM01", "organismo_politicas_mulheres"), ("MPPM24a1", "centro_referencia"), ("MPPM20", "casa_abrigo")],
    "Segurança Pública": [("MSEG168", "delegacia_mulher")],
}


def main(xlsx):
    from openpyxl import load_workbook
    wb = load_workbook(xlsx, read_only=True)
    dados = {}
    for aba, vars_ in VARIAVEIS.items():
        linhas = wb[aba].iter_rows(values_only=True)
        cab = [str(c) for c in next(linhas)]
        idx = {v: cab.index(v) for v, _ in vars_}
        for r in linhas:
            if r[0] and str(r[0]).startswith("25"):          # CodMun da Paraíba
                d = dados.setdefault(str(r[0]), {"municipio": r[3]})
                for v, col in vars_:
                    d[col] = r[idx[v]]
    confere(len(dados) == TOTAL_MUNICIPIOS, f"MUNIC 2023: {len(dados)} municípios da PB (esperado {TOTAL_MUNICIPIOS})")
    cols = ["municipio"] + [c for vs in VARIAVEIS.values() for _, c in vs]
    with open(RAIZ / "dados" / "brutos" / "ibge_munic2023_rede_atendimento_pb.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cod_ibge7"] + cols)
        for cod in sorted(dados):
            w.writerow([cod] + [dados[cod][c] for c in cols])
    print(f"MUNIC 2023 extraída: {len(dados)} municípios")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except (Falha, IndexError) as e:
        print(f"ERRO: {e or 'informe o caminho da planilha Base_MUNIC_2023.xlsx'}")
        sys.exit(1)
