# Tarefas do teste com usuários e respostas certas

Gerado por `testes/gerar_material_teste.py` a partir de `web/dados.json`. Fonte: SINAN/TABNET (notificações de mulheres, município de residência, sem violência autoprovocada) e IBGE Censo 2022. Não altere os números à mão: se o dados.json mudar, rode o script de novo.

**Para o participante:** leia só a coluna "Tarefa", em voz alta, uma de cada vez. Todas começam na página inicial do painel (Mapa).
**Para quem conduz:** a resposta certa e o critério de acerto ficam só nesta folha; não mostre ao participante.

## T1 · Gestora estadual

**Tarefa:** A Secretaria quer saber onde a notificação está mais abaixo do esperado. Encontre os 3 municípios com o menor valor de observado ÷ esperado, considerando só os que têm pelo menos 10 casos (todos os tipos, 2019 a 2024).

**Resposta certa:** 1º Sousa (0,09; 15 casos); 2º Aroeiras (0,21; 10 casos); 3º Brejo do Cruz (0,28; 10 casos)

**Critério:** Acerto: os 3 nomes, em qualquer ordem. Parcial: 1 ou 2 nomes. Tempo-limite sugerido: 3 min.

## T2 · Gestora municipal

**Tarefa:** Você trabalha em Sousa. Abra a ficha do município e diga se a taxa de notificação está acima ou abaixo da média do estado.

**Resposta certa:** Abaixo. Sousa: 7,2 por 100 mil mulheres por ano; estado: 83,9 (observado ÷ esperado = 0,09).

**Critério:** Acerto: dizer "abaixo" (ou "notifica menos") olhando a ficha. Tempo-limite sugerido: 3 min.

## T3 · Técnico da vigilância

**Tarefa:** Em Campina Grande, qual faixa etária tem mais casos notificados (2019 a 2024)?

**Resposta certa:** 20 a 29 anos: 146 de 691 casos (21%).

**Critério:** Acerto: a faixa certa. As faixas têm larguras diferentes (ex.: 10 a 14 e 20 a 29); vale a contagem mostrada. Tempo-limite sugerido: 3 min.

## T4 · Técnico da vigilância

**Tarefa:** No estado, a violência sexual notificada cresceu de 2019 para 2024?

**Resposta certa:** Sim, cresceu: de 423 casos em 2019 para 675 em 2024 (+60%).

**Critério:** Acerto: "sim" com base no painel (gráfico, conclusões ou filtro do mapa). Tempo-limite sugerido: 3 min.

## T5 · Todos

**Tarefa:** Você vai levar os dados para uma reunião. Baixe a tabela dos municípios ou imprima a ficha de um município.

**Resposta certa:** Arquivo CSV com 223 municípios (aba Análise → Baixar CSV) ou ficha impressa/salva em PDF (ficha → Imprimir ficha).

**Critério:** Acerto: arquivo baixado ou janela de impressão aberta com a ficha. Tempo-limite sugerido: 3 min.

## Caminho mais curto no painel (teste-piloto automatizado)

| Tarefa | Ações | Caminho |
|---|---|---|
| T1 | 2 | Indicador "Observado ÷ esperado" → ranking "10 menores" |
| T2 | 1 | Buscar município: digitar "Sousa" e Enter (a ficha mostra a taxa, a média do estado e "Notifica menos que a média do estado") |
| T3 | 1 | Buscar "Campina Grande" e Enter (a ficha escreve "Faixa mais atingida: …") |
| T4 | 1 | Aba Análise (bloco "O que os dados mostram") |
| T5 | 2 | Aba Análise → Baixar CSV; ou buscar o município → Imprimir ficha |

Fonte: `testes/testar_usabilidade.py` (registro em `capturas/piloto_tarefas.json`, gerado pelos testes).
