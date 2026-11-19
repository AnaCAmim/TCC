"""Gera a parte do material do teste com usuários que depende dos dados (docs/teste_usuarios/ deste repositório):
- respostas.json e 02_tarefas_e_respostas.md: as 5 tarefas com a resposta certa calculada do web/dados.json;
- planilha_registro.xlsx: registro de acerto, tempo e observações por tarefa, questionário SUS com a nota por fórmula e resumo.
Rodar de novo sempre que o dados.json mudar (o testar_usabilidade.py avisa).
Uso: python testes/gerar_material_teste.py   (requer: pip install openpyxl)"""
import json
import pathlib
import sys

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from respostas_tarefas import respostas_certas  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "docs" / "teste_usuarios"
SAIDA.mkdir(parents=True, exist_ok=True)
DADOS = json.loads((RAIZ / "web" / "dados.json").read_text(encoding="utf-8"))
R = respostas_certas(DADOS)
N_PART = 5        # participantes previstos no plano (docs/websig_plano.md, seção 3)
LINHAS_EXTRA = 5  # linhas de reserva para participantes a mais


def fmt(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


faixa = lambda f: f.replace("-", " a ") + " anos"
t1 = R["T1"]["municipios"]
TAREFAS = [
    ("T1", "Gestora estadual",
     "A Secretaria quer saber onde a notificação está mais abaixo do esperado. Encontre os 3 municípios com o menor valor de "
     "observado ÷ esperado, considerando só os que têm pelo menos 10 casos (todos os tipos, 2019 a 2024).",
     "; ".join(f"{i + 1}º {m['nome']} ({fmt(m['oe'], 2)}; {m['casos']} casos)" for i, m in enumerate(t1)),
     "Acerto: os 3 nomes, em qualquer ordem. Parcial: 1 ou 2 nomes."),
    ("T2", "Gestora municipal",
     "Você trabalha em Sousa. Abra a ficha do município e diga se a taxa de notificação está acima ou abaixo da média do estado.",
     f"Abaixo. Sousa: {fmt(R['T2']['taxa_sousa'], 1)} por 100 mil mulheres por ano; estado: {fmt(R['T2']['taxa_estado'], 1)} "
     f"(observado ÷ esperado = {fmt(R['T2']['oe'], 2)}).",
     "Acerto: dizer \"abaixo\" (ou \"notifica menos\") olhando a ficha."),
    ("T3", "Técnico da vigilância",
     "Em Campina Grande, qual faixa etária tem mais casos notificados (2019 a 2024)?",
     f"{' e '.join(faixa(f) for f in R['T3']['faixas'])}: {fmt(R['T3']['casos'])} de {fmt(R['T3']['total_cg'])} casos ({R['T3']['pct']}%).",
     "Acerto: a faixa certa. As faixas têm larguras diferentes (ex.: 10 a 14 e 20 a 29); vale a contagem mostrada."),
    ("T4", "Técnico da vigilância",
     "No estado, a violência sexual notificada cresceu de 2019 para 2024?",
     f"Sim, cresceu: de {fmt(R['T4']['sexual_2019'])} casos em 2019 para {fmt(R['T4']['sexual_2024'])} em 2024 (+{R['T4']['variacao_pct']}%).",
     "Acerto: \"sim\" com base no painel (gráfico, conclusões ou filtro do mapa)."),
    ("T5", "Todos",
     "Você vai levar os dados para uma reunião. Baixe a tabela dos municípios ou imprima a ficha de um município.",
     f"Arquivo CSV com {R['T5']['linhas_csv']} municípios (aba Análise → Baixar tabela (CSV)) ou ficha impressa/salva em PDF (ficha → Imprimir ficha).",
     "Acerto: arquivo baixado ou janela de impressão aberta com a ficha."),
]

# ---------------- respostas.json e tarefas em markdown ----------------
(SAIDA / "respostas.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
md = ["# Tarefas do teste com usuários e respostas certas", "",
      f"Gerado por `testes/gerar_material_teste.py` a partir de `web/dados.json`. Fonte: {DADOS.get('fonte', 'SINAN/TABNET e Censo 2022')}. "
      "Não altere os números à mão: se o dados.json mudar, rode o script de novo.", "",
      "**Para o participante:** leia só a coluna \"Tarefa\", em voz alta, uma de cada vez. Todas começam na página inicial do painel (Mapa).",
      "**Para quem conduz:** a resposta certa e o critério de acerto ficam só nesta folha; não mostre ao participante.", ""]
for cod, persona, txt, resp, crit in TAREFAS:
    md += [f"## {cod} · {persona}", "", f"**Tarefa:** {txt}", "", f"**Resposta certa:** {resp}", "", f"**Critério:** {crit} Tempo-limite sugerido: 3 min.", ""]
md += ["## Caminho mais curto no painel (teste-piloto automatizado)", "",
       "| Tarefa | Ações | Caminho |", "|---|---|---|",
       "| T1 | 2 | Indicador \"Observado ÷ esperado\" → ranking \"10 menores\" |",
       "| T2 | 1 | Buscar município: digitar \"Sousa\" e Enter (a ficha mostra a taxa, a média do estado e \"Notifica menos que a média do estado\") |",
       "| T3 | 1 | Buscar \"Campina Grande\" e Enter (a ficha escreve \"Faixa mais atingida: …\") |",
       "| T4 | 1 | Aba Análise (bloco \"Leituras prontas\") |",
       "| T5 | 2 | Aba Análise → Baixar tabela (CSV); ou buscar o município → Imprimir ficha |", "",
       "Na primeira visita, a tela \"Sobre o painel\" abre sozinha e fecha com 1 clique (Começar): é 1 ação a mais, só uma vez.", "",
       "Fonte: `testes/testar_usabilidade.py` (registro em `capturas/piloto_tarefas.json`, gerado pelos testes).", ""]
(SAIDA / "02_tarefas_e_respostas.md").write_text("\n".join(md), encoding="utf-8")

# ---------------- planilha de registro ----------------
F = "Arial"
fonte, negrito, titulo = Font(name=F, size=10), Font(name=F, size=10, bold=True), Font(name=F, size=13, bold=True)
cab_fill = PatternFill("solid", start_color="E7E6F7")
entrada = PatternFill("solid", start_color="FFF2CC")
fino = Side(style="thin", color="BFBFBF")
borda = Border(left=fino, right=fino, top=fino, bottom=fino)
quebra = Alignment(wrap_text=True, vertical="top")


def cabecalho(ws, linha, nomes, larguras):
    for i, (n, w) in enumerate(zip(nomes, larguras), start=1):
        c = ws.cell(row=linha, column=i, value=n)
        c.font, c.fill, c.border, c.alignment = negrito, cab_fill, borda, Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = w
    ws.freeze_panes = ws.cell(row=linha + 1, column=1)


wb = Workbook()

# Instruções
ws = wb.active; ws.title = "Instruções"
ws.column_dimensions["A"].width = 110
linhas = [
    ("Planilha de registro do teste com usuários: painel de violência contra a mulher na Paraíba", titulo),
    ("Células em AMARELO são para preencher. As demais têm fórmulas: não apague.", negrito),
    ("Aba Tarefas: uma linha por participante e tarefa (P01 a P05 já listados; há linhas de reserva).", fonte),
    ("  Acerto: escolha Sim, Parcial ou Não. Tempo: segundos entre ler a tarefa e dar a resposta (ou desistir). Ajuda: Sim se quem conduz precisou ajudar.", fonte),
    ("  Observações: o que a pessoa disse em voz alta, onde hesitou, caminho que tentou.", fonte),
    ("Aba SUS: as 10 notas (1 = discordo fortemente, 5 = concordo fortemente). A nota SUS (0 a 100) sai sozinha quando as 10 estiverem preenchidas.", fonte),
    ("  Fórmula (Brooke, 1996): ((Q1−1)+(5−Q2)+(Q3−1)+(5−Q4)+(Q5−1)+(5−Q6)+(Q7−1)+(5−Q8)+(Q9−1)+(5−Q10)) × 2,5.", fonte),
    ("Aba Abertas: respostas às 2 perguntas finais. Aba Respostas certas: gabarito (não mostrar ao participante).", fonte),
    ("Aba Resumo: taxa de acerto e tempo por tarefa, nota SUS média. Atualiza sozinha.", fonte),
    ("", fonte),
    ("Exemplo de preenchimento (não é dado real; não copie para as outras abas):", negrito),
    ("  Tarefas → P01 | T2 | Sim | 48 | Não | \"Achei pela busca; li 'notifica menos que a média'.\"", fonte),
    ("  SUS → P01 | 4 | 2 | 4 | 1 | 4 | 2 | 5 | 2 | 4 | 2  → nota calculada 80,0", fonte),
]
for i, (t, f) in enumerate(linhas, start=1):
    c = ws.cell(row=i, column=1, value=t); c.font = f; c.alignment = Alignment(wrap_text=True)

# Tarefas
ws = wb.create_sheet("Tarefas")
cabecalho(ws, 1, ["Participante", "Tarefa", "Acerto (Sim/Parcial/Não)", "Tempo (s)", "Pediu ajuda (Sim/Não)", "Resposta dada", "Observações"], [13, 9, 15, 11, 13, 34, 60])
dv_acerto = DataValidation(type="list", formula1='"Sim,Parcial,Não"', allow_blank=True)
dv_sn = DataValidation(type="list", formula1='"Sim,Não"', allow_blank=True)
dv_tempo = DataValidation(type="decimal", operator="between", formula1="0", formula2="1800", allow_blank=True)
dv_tempo.error = "Tempo em segundos (0 a 1800)."
for dv in (dv_acerto, dv_sn, dv_tempo):
    ws.add_data_validation(dv)
lin = 2
for k in range(1, N_PART + LINHAS_EXTRA + 1):
    for cod, *_ in TAREFAS:
        ws.cell(row=lin, column=1, value=f"P{k:02d}"); ws.cell(row=lin, column=2, value=cod)
        for col in range(1, 8):
            c = ws.cell(row=lin, column=col); c.font, c.border = fonte, borda
            if col >= 3:
                c.fill = entrada
            if col >= 6:
                c.alignment = quebra
        lin += 1
ULT_T = lin - 1
dv_acerto.add(f"C2:C{ULT_T}"); dv_sn.add(f"E2:E{ULT_T}"); dv_tempo.add(f"D2:D{ULT_T}")
ws["D1"].comment = Comment("Segundos entre ler a tarefa e responder ou desistir. Tempo-limite sugerido: 180 s.", "roteiro")

# SUS
ws = wb.create_sheet("SUS")
ITENS = [  # versão brasileira validada: Lourenço, Carmona e Lopes (2022), Aquichan 22(2):e2228, Tabela 1
    "Eu acho que gostaria de usar esse sistema frequentemente.", "Eu achei esse sistema desnecessariamente complexo.",
    "Eu achei esse sistema fácil de usar.", "Eu achei que precisaria de ajuda de uma pessoa técnica para ser capaz de usar esse sistema.",
    "Eu achei que as várias funções desse sistema foram bem integradas.", "Eu acho que o sistema apresenta muita inconsistência.",
    "Eu imagino que a maioria das pessoas pode aprender a usar esse sistema rapidamente.", "Eu achei esse sistema muito pesado para usar.",
    "Eu me senti muito seguro usando o sistema.", "Eu precisei aprender muitas coisas antes que pudesse utilizar esse sistema."]
cabecalho(ws, 1, ["Participante"] + [f"Q{i}" for i in range(1, 11)] + ["Nota SUS (0–100)"], [13] + [6] * 10 + [14])
for i, t in enumerate(ITENS, start=2):
    ws.cell(row=1, column=i).comment = Comment(t, "SUS")
dv_q = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True)
dv_q.error = "Nota de 1 (discordo fortemente) a 5 (concordo fortemente)."
ws.add_data_validation(dv_q)
for k in range(1, N_PART + LINHAS_EXTRA + 1):
    r = k + 1
    ws.cell(row=r, column=1, value=f"P{k:02d}")
    for col in range(1, 13):
        c = ws.cell(row=r, column=col); c.font, c.border = fonte, borda
        if 2 <= col <= 11:
            c.fill, c.alignment = entrada, Alignment(horizontal="center")
    ws.cell(row=r, column=12, value=(f'=IF(COUNT(B{r}:K{r})=10,((B{r}-1)+(5-C{r})+(D{r}-1)+(5-E{r})+(F{r}-1)+(5-G{r})'
                                      f'+(H{r}-1)+(5-I{r})+(J{r}-1)+(5-K{r}))*2.5,"")')).number_format = "0.0"
ULT_S = N_PART + LINHAS_EXTRA + 1
dv_q.add(f"B2:K{ULT_S}")
ws.cell(row=ULT_S + 2, column=1, value="Passe o mouse no cabeçalho Q1…Q10 para ver a afirmação. Itens ímpares são positivos; pares, negativos.").font = Font(name=F, size=9, italic=True)

# Abertas
ws = wb.create_sheet("Abertas")
cabecalho(ws, 1, ["Participante", "Cargo / função (sem nome)", "O que faltou para usar no seu trabalho?", "O que confundiu?"], [13, 26, 60, 60])
for k in range(1, N_PART + LINHAS_EXTRA + 1):
    ws.cell(row=k + 1, column=1, value=f"P{k:02d}")
    for col in range(1, 5):
        c = ws.cell(row=k + 1, column=col); c.font, c.border, c.alignment = fonte, borda, quebra
        if col >= 2:
            c.fill = entrada

# Respostas certas (gabarito)
ws = wb.create_sheet("Respostas certas")
cabecalho(ws, 1, ["Tarefa", "Persona", "Tarefa lida ao participante", "Resposta certa", "Critério de acerto"], [8, 18, 60, 55, 45])
for i, t in enumerate(TAREFAS, start=2):
    for col, v in enumerate(t, start=1):
        c = ws.cell(row=i, column=col, value=v); c.font, c.border, c.alignment = fonte, borda, quebra
ws.cell(row=8, column=1, value="Fonte: respostas calculadas do web/dados.json por testes/gerar_material_teste.py (SINAN/TABNET 2019–2024; mulheres no Censo 2022).").font = Font(name=F, size=9, italic=True)

# Resumo
ws = wb.create_sheet("Resumo")
cabecalho(ws, 1, ["Tarefa", "Participantes com registro", "Acertos (Sim)", "Parciais", "Taxa de acerto", "Tempo médio (s)", "Tempo mediano (s)", "Pediram ajuda"], [10, 16, 12, 10, 13, 14, 15, 13])
rg = lambda col: f"Tarefas!${col}$2:${col}${ULT_T}"
for i, (cod, *_) in enumerate(TAREFAS, start=2):
    ws.cell(row=i, column=1, value=cod)
    ws.cell(row=i, column=2, value=f'=COUNTIFS({rg("B")},A{i},{rg("C")},"<>")')
    ws.cell(row=i, column=3, value=f'=COUNTIFS({rg("B")},A{i},{rg("C")},"Sim")')
    ws.cell(row=i, column=4, value=f'=COUNTIFS({rg("B")},A{i},{rg("C")},"Parcial")')
    ws.cell(row=i, column=5, value=f'=IF(B{i}=0,"",C{i}/B{i})').number_format = "0%"
    ws.cell(row=i, column=6, value=f'=IF(COUNTIFS({rg("B")},A{i},{rg("D")},"<>")=0,"",AVERAGEIFS({rg("D")},{rg("B")},A{i}))').number_format = "0"
    # mediana condicional: fórmula de matriz
    ws[f"G{i}"] = ArrayFormula(f"G{i}", f'=IF(COUNTIFS({rg("B")},A{i},{rg("D")},"<>")=0,"",MEDIAN(IF(({rg("B")}=A{i})*({rg("D")}<>""),{rg("D")})))')
    ws[f"G{i}"].number_format = "0"
    ws.cell(row=i, column=8, value=f'=COUNTIFS({rg("B")},A{i},{rg("E")},"Sim")')
    for col in range(1, 9):
        c = ws.cell(row=i, column=col); c.font, c.border = fonte, borda
sus = f"SUS!$L$2:$L${ULT_S}"
extra = [("Questionários SUS completos", f"=COUNT({sus})", "0"), ("Nota SUS média", f'=IF(COUNT({sus})=0,"",AVERAGE({sus}))', "0.0"),
         ("Nota SUS mínima", f'=IF(COUNT({sus})=0,"",MIN({sus}))', "0.0"), ("Nota SUS máxima", f'=IF(COUNT({sus})=0,"",MAX({sus}))', "0.0")]
for j, (rot, fo, nfmt) in enumerate(extra, start=9):
    ws.cell(row=j, column=1, value=rot).font = negrito
    ws.merge_cells(start_row=j, start_column=1, end_row=j, end_column=3)
    c = ws.cell(row=j, column=4, value=fo); c.font, c.number_format, c.border = fonte, nfmt, borda
ws.cell(row=14, column=1, value="Leitura: a média 68, muito citada, ainda não foi conferida na fonte original [VERIFICAR]. Com 5 participantes, a média é só indicativa. Itens: versão brasileira de Lourenço, Carmona e Lopes (2022).").font = Font(name=F, size=9, italic=True)

wb.save(SAIDA / "planilha_registro.xlsx")
print("Material gerado em", SAIDA)
