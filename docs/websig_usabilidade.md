# Revisão de usabilidade e acessibilidade do painel (18/11/2026, atualizada até 22/11/2026)

Revisão do painel pelas 10 heurísticas de Nielsen e pela WCAG 2.1 nível AA, antes do teste com usuários. Nenhum dado, SQL, fórmula ou indicador foi alterado; as mudanças são só de interface (`web/index.html`, `css/painel.css`, `js/mapa.js`, `js/app.js`).

Como foi feita: inspeção do código e das telas, mais medições automáticas com Playwright (`testes/testar_usabilidade.py`, dentro do `atualizar.bat`). Depois, os testes do painel e de usabilidade passaram também no Firefox e no WebKit, o motor do Safari (`testar_navegadores.bat`). Não houve teste com leitor de tela real (NVDA, VoiceOver) nem em Safari de verdade (Mac ou iPhone).

Escala de gravidade (Nielsen): 0 = não é problema; 1 = cosmético; 2 = pequeno; 3 = grande, corrigir antes do teste; 4 = catástrofe, impede a tarefa.

## Problemas encontrados e correções

| # | Problema | Heurística / critério | Gravidade | Correção feita |
|---|---|---|---|---|
| 1 | Busca por um nome inexistente não dava nenhum retorno: a pessoa não sabia se o painel travou ou se errou o nome. | H9 Ajudar a reconhecer e corrigir erros; H1 Visibilidade do estado | 3 | Mensagem abaixo da busca: "Nenhum município encontrado para "…". Confira o nome (acentos e maiúsculas não importam)", anunciada a leitores de tela (`aria-live`). |
| 2 | No celular, o mapa só aparecia depois dos filtros **e** do ranking inteiro (a 1.166 px do topo, em 320 px de largura). | H8 Estética e design minimalista; WCAG 1.3.2 Sequência significativa | 3 | Filtros e ranking separados em dois blocos; no celular a ordem é filtros → mapa → ranking. O mapa começa a 672 px numa tela de 390×844 (visível sem rolar) e a 826 px numa de 320×640. |
| 3 | Para dizer a faixa etária mais atingida (T3) era preciso comparar 11 barras de larguras parecidas. | H6 Reconhecer em vez de lembrar | 2 | A ficha escreve a frase "Faixa mais atingida: 20 a 29 anos (146 casos, 21%)". Empates aparecem juntos (ex.: Sousa, "20 a 29 anos e 30 a 39 anos, 4 casos cada"). A faixa "Ignorada" não entra. |
| 4 | O botão "Copiar link" ficava dentro da lista de abas (`role=tablist`): o leitor de tela o anunciava como uma aba. | WCAG 4.1.2 Nome, função, valor | 2 | Botão movido para fora da lista de abas. |
| 5 | O mapa tinha `role="application"`, que faz leitores de tela desligarem os atalhos de navegação dentro dele. | WCAG 4.1.2 Nome, função, valor | 2 | Trocado por `role="region"` com rótulo. A alternativa acessível ao mapa continua sendo "Ver como tabela", a busca e o ranking. |
| 6 | Sem atalho para pular o cabeçalho: quem usa teclado passava por todas as abas antes de chegar aos filtros. | WCAG 2.4.1 Pular blocos | 2 | Link "Pular para o conteúdo", que aparece no primeiro Tab. |
| 7 | Ao fechar a ficha, o foco do teclado se perdia (voltava para o início da página). | WCAG 2.4.3 Ordem do foco | 2 | O foco volta para onde estava (o item do ranking ou o campo de busca); se ele sumiu, vai para o título do mapa. |
| 8 | Botões de zoom do mapa com 30 px: pequenos para o dedo no celular. | WCAG 2.5.5 Tamanho do alvo (AAA, adotado como meta); H7 Flexibilidade | 2 | Botões de zoom com 44 × 44 px. |
| 9 | Esc não fechava a ficha do município (só a janela de comparação). | H3 Controle e liberdade do usuário | 1 | Esc fecha a ficha (fora de campos de texto e quando a comparação não está aberta). |
| 10 | Os botões "10 maiores / 10 menores" usavam `role=tab` sem painel correspondente. | WCAG 4.1.2 Nome, função, valor | 1 | Viraram botões alternáveis (`aria-pressed`); a lista recebe o rótulo "10 maiores valores" ou "10 menores valores, só municípios com pelo menos 10 casos". |
| 11 | O título da aba do navegador era sempre o mesmo, em qualquer tela ou ficha. | WCAG 2.4.2 Página com título; H1 Visibilidade do estado | 1 | O título acompanha a tela: "Mapa · …", "Análise · …", "Sousa · …". |
| 12 | As abas principais não respondiam às setas, como manda o padrão de abas. | WCAG 2.1.1 Teclado; H4 Consistência e padrões | 1 | Setas ← e → trocam de aba; só a aba ativa entra na ordem do Tab. |
| 13 | Os painéis das abas tinham rótulo próprio, desligado do botão da aba. | WCAG 1.3.1 Informação e relações | 1 | Painéis ligados às abas por `aria-labelledby`. |
| 14 | A dica do mapa (nome e valor) só aparecia ao passar o mouse; no toque e no teclado não havia dica, e os municípios do mapa não recebiam foco. | WCAG 1.4.13 Conteúdo em foco ou passagem do mouse; 2.1.1 Teclado; H6 | 1 | **Corrigido.** Tab percorre os municípios do mapa em ordem alfabética (só os da região escolhida, se houver filtro); a mesma etiqueta "nome · valor" aparece acima do município, sem cobri-lo, com "Enter abre a ficha"; Enter ou espaço abre a ficha e Esc a fecha, devolvendo o foco ao município. No toque, o 1º toque mostra a etiqueta ("Toque de novo para abrir a ficha") e o 2º abre a ficha. Cada município tem `role=button` e rótulo "Nome: valor". Testado no Chrome, Firefox e WebKit. |
| 15 | No Safari (WebKit), o Tab pula links por padrão: o "Pular para o conteúdo", o ranking e os links "como calcular" ficavam fora do teclado. | WCAG 2.1.1 Teclado | 2 | `tabindex="0"` explícito nesses links . |
| 16 | No Firefox, com a lista de sugestões aberta num campo da comparação, o 1º Esc fecha a lista e só o 2º fecha a janela. | H3 Controle e liberdade | 0 | Comportamento do navegador; não corrigido. O botão Fechar continua disponível. |

## O que foi conferido e passou

| Item | Critério | Resultado |
|---|---|---|
| Contraste do texto, tema claro | WCAG 1.4.3 (mínimo 4,5:1) | Menor contraste: 4,77:1 (texto terciário sobre o fundo cinza). Texto principal: 19,2:1. |
| Contraste do texto, tema escuro | WCAG 1.4.3 | Menor: 5,9:1. Texto principal: 15,2:1. |
| Foco visível | WCAG 2.4.7 e 1.4.11 (3:1) | Contorno na cor de destaque: 7,5:1 (claro) e 8,1:1 (escuro). Todos os controles mostram o contorno ao receber o foco. |
| Paleta do mapa para daltonismo | Simulação de Machado, Oliveira e Fernandes (2009) [VERIFICAR referência completa] | Menor diferença de cor (ΔE, CIELAB) entre classes vizinhas: sequencial 10,0 (tritanopia); divergente 11,4 (protanopia, escuro). Todas acima de 10, o que separa bem as classes. A legenda também traz o intervalo em texto. |
| Cor não é a única informação | WCAG 1.4.1 | Legenda com intervalos escritos, título do mapa com os filtros, tabela e ficha com os números. |
| Tabela como alternativa ao mapa | WCAG 1.1.1 | "Ver como tabela" mostra os 223 municípios com os mesmos filtros; a tabela da Análise baixa em CSV. |
| Celular e zoom de 400% | WCAG 1.4.10 Refluxo (320 px) | Sem rolagem lateral em 320 px; testado também em 390×844. |
| Teclado | WCAG 2.1.1 | Todos os controles alcançáveis com Tab; ranking abre a ficha com Enter; comparação e ordenação da tabela só com teclado (testar_front.py). |
| Controles com nome | WCAG 4.1.2 | Nenhum botão, link ou campo sem nome acessível. |
| Aviso de poucos casos e "notificação ≠ ocorrência" | H5 Prevenção de erros (de leitura) | Já existiam; mantidos. |

## Teste-piloto automatizado das tarefas (T1–T5)

Cada tarefa parte da página inicial (Mapa, sem município aberto). Uma ação = um clique, uma escolha numa lista ou digitar um nome e teclar Enter. A resposta na tela foi comparada com a resposta calculada diretamente do `web/dados.json`.

| Tarefa | Ações | Caminho | Resposta na tela (= dados.json) |
|---|---|---|---|
| T1 · 3 menores O/E com pelo menos 10 casos | 2 | Indicador "Observado ÷ esperado" → "10 menores" | Sousa 0,09; Aroeiras 0,21; Brejo do Cruz 0,28 |
| T2 · Sousa acima ou abaixo da média | 1 | Buscar "Sousa" + Enter | Abaixo: 7,2 contra 83,9 por 100 mil mulheres por ano; "Notifica menos que a média do estado" |
| T3 · faixa mais atingida em Campina Grande | 1 | Buscar "Campina Grande" + Enter | 20 a 29 anos (146 casos, 21%) |
| T4 · a violência sexual cresceu de 2019 a 2024? | 1 | Aba Análise | Sim: de 423 para 675 casos (+60%) |
| T5 · baixar a tabela | 2 | Aba Análise → Baixar CSV | CSV com 223 municípios |
| T5 · imprimir a ficha | 2 | Buscar o município + Enter → Imprimir ficha | Folha limpa com a ficha |

Nenhuma tarefa passou de 4 ações, por isso nenhuma precisou ser simplificada. As contagens já eram as mesmas antes desta revisão; o que mudou foi a T3, que agora se responde lendo uma frase em vez de comparar 11 barras (problema 3), e a busca, que avisa quando não acha o município (problema 1).

Limite do piloto: o robô sabe onde clicar. Ele mede o caminho mais curto, não se uma pessoa o encontra. Isso só o teste com usuários (`docs/teste_usuarios/`) mostra.

Registro: `capturas/piloto_tarefas.json` (gerado pelos testes) e capturas `piloto_T1.png` … `piloto_T4.png`, `piloto_celular_320.png`.

## Pendências

- Teste com leitor de tela real (NVDA no Windows) e em Safari de verdade (Mac ou iPhone); Firefox e WebKit já passam nos testes automáticos.
- Com o Tab, os 223 municípios do mapa vêm depois do ranking; quem não quiser percorrê-los pode usar a busca ou "Ver como tabela". Com filtro de região, só os municípios da região entram no Tab.
- Teste com 5 usuários do público-alvo (roteiro, tarefas, SUS e planilha em `docs/teste_usuarios/`). [CONFIRMAR COM ORIENTADOR] a necessidade de Comitê de Ética.
- Referências de apoio para o artigo [VERIFICAR]: NIELSEN, J. *Usability engineering*. Boston: Academic Press, 1993; W3C. *Web Content Accessibility Guidelines (WCAG) 2.1*. 2018; MACHADO, G. M.; OLIVEIRA, M. M.; FERNANDES, L. A. F. A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, v. 15, n. 6, p. 1291–1298, 2009.

## Compatibilidade entre navegadores

| Navegador (Playwright) | testar_front.py | testar_usabilidade.py | Ajustes feitos |
|---|---|---|---|
| Chrome instalado | 85 OK, 0 falhas (inclui Copiar link) | 28 OK, 0 falhas | — |
| Firefox | 84 OK, 0 falhas | 28 OK, 0 falhas | Nenhum no painel. No teste: o 1º Esc fecha a lista de sugestões do campo (problema 16). O Firefox do Playwright não emula `is_mobile`; o celular foi testado com tela pequena e toque. |
| WebKit (motor do Safari) | 84 OK, 0 falhas | 28 OK, 0 falhas | Links com `tabindex="0"` (problema 15). No teste: o toque usa um ponto dentro do polígono, porque o centro da caixa pode cair no município vizinho. |

A leitura da área de transferência (Copiar link) e o PDF da ficha só são conferidos no Chrome, porque os outros navegadores do Playwright não liberam essas funções nos testes.

## Acabamento para a apresentação (18/11/2026)

Revisão de acabamento feita como faria uma banca de Interface com o Usuário, sem novas bases nem indicadores e sem mudar dados, SQL ou fórmulas.

| # | Problema | Heurística / critério | Gravidade | Ajuste feito |
|---|---|---|---|---|
| A1 | Quem chegava pela primeira vez não tinha uma explicação do painel: para que serve, como usar, fontes e avisos. | H10 Ajuda e documentação; H2 Correspondência com o mundo real | 3 | Tela **"Sobre o painel"**: abre na 1ª visita, com para que serve, uso em 3 passos, os 5 indicadores em uma linha cada, fontes com data e os avisos (notificação ≠ ocorrência; poucos casos). Fecha com um clique ("Começar") e não volta (localStorage com try/catch). Botão "Sobre o painel" no topo. Não abre quando se chega por link de uma ficha. |
| A2 | A ficha não dizia o que olhar primeiro: começava por 5 cartões do mesmo peso. | H8 Estética e design minimalista; hierarquia visual | 3 | **Frase-resumo calculada** no topo (ex.: "Notifica bem menos que o estado: 0,09 do esperado (todos os tipos, 2019 a 2024)"), com os mesmos cortes da legenda (0,5 · 0,8 · 1,25 · 2). Depois "Os 5 indicadores" e, em seguida, os contextos: faixa etária em detalhe, casos por ano, onde foram atendidas e serviços da MUNIC. |
| A3 | No celular, a ficha era um rolo longo. | H8; WCAG 1.4.10 Refluxo | 2 | Seções recolhíveis (`<details>`); no celular, só "Os 5 indicadores" começa aberta. Na impressão, todas abrem. |
| A4 | Sem aviso de carregamento: a tela ficava vazia enquanto os dados chegavam. | H1 Visibilidade do estado do sistema | 2 | "Carregando os dados do painel…" (`role=status`), sobreposto e sem deslocar o layout. |
| A5 | Se `dados.json` e `dados.js` faltassem, aparecia uma faixa vermelha genérica, com cores fixas que ignoravam o tema escuro. | H9 Ajudar a reconhecer e corrigir erros | 3 | Tela de erro com o que aconteceu e o que fazer (conferir a pasta, extrair o .zip inteiro, rodar `atualizar.bat`) e o botão "Tentar de novo"; usa as cores do tema. |
| A6 | Filtrar a tabela da Análise por um nome inexistente deixava a tabela vazia, sem explicação. | H9; estados vazios | 2 | Linha "Nenhum município encontrado para …. Confira o nome." |
| A7 | Termos diferentes para a mesma coisa: "Taxa por 100 mil mulheres" (lista e título do mapa) × "por ano" (legenda); "Taxa / 100 mil / ano" nas tabelas; "Comparar com outros" × "Comparar municípios"; dois "Copiar link" com funções diferentes; "Baixar CSV". | H4 Consistência e padrões | 2 | Nome completo "Taxa por 100 mil mulheres por ano" na lista e no título do mapa; "Taxa por 100 mil/ano" nos cabeçalhos curtos; "Comparar municípios" nos dois lugares; "Copiar link da ficha" na ficha; "Baixar tabela (CSV)". |
| A8 | Números sem unidade nos gráficos da Análise: a contagem por faixa ("2.592 (25,1%)"), a taxa por faixa e a linha de referência. | Nenhum número sem unidade; H2 | 2 | "2.592 casos (25,1%)", "157,9 por 100 mil/ano · 1.315 casos", "estado: 83,9 por 100 mil/ano", "10.344 casos · 83,9 por 100 mil/ano". |
| A9 | As leituras da Análise não cobriam os contextos novos nem diziam o que fazer com cada achado. | H2; utilidade para a decisão | 2 | 3 leituras novas, todas calculadas dos dados: faixa de maior taxa (10 a 14 anos), % atendidas na própria região de saúde e quantos municípios declaram cada serviço na MUNIC 2023. **Toda** leitura ganhou "Pergunta para a gestão". O título do bloco passou a "Leituras prontas". |
| A10 | Não havia roteiro para demonstrar o painel em poucos minutos. | H10; apoio à apresentação | 1 | Botão **"Tour"**: 6 passos (mapa da taxa → observado ÷ esperado → ficha de Sousa → faixa etária em taxa → Análise → Como calcular), cada um com uma frase, Anterior/Próximo, setas ← → e Esc; ao sair, o foco volta ao botão. |
| A11 | Abrir o painel montava as três telas de uma vez: no celular simulado, 380 ms de bloqueio e Desempenho 75 no Lighthouse. | Eficiência; tempo de resposta | 2 | Análise e Como calcular só são montadas na primeira vez que se abre a aba; "Sobre o painel" abre sem esperar os dados; o aviso de carregamento não desloca o layout; meta description. Lighthouse: celular 99, computador 100 (ver `docs/lighthouse/`). |

Teste-piloto depois do acabamento: as tarefas continuam com 1 ou 2 ações. Na primeira visita há 1 ação a mais (fechar "Sobre o painel"), só uma vez.

## Visual de relatório técnico (20/11/2026)

Objetivo: tirar a aparência de interface genérica e dar ao painel o visual de relatório técnico / jornalismo de dados. Dados, SQL, fórmulas, indicadores, funções e a estrutura das 3 telas não mudaram.

### Visual (antes → depois)

| # | Elemento | Antes | Depois |
|---|---|---|---|
| V1 | Cor institucional | Roxo (#5b3fa8) em abas ativas, botões principais, faixas laterais e ícones | Azul-petróleo escuro (#0e4f5c; no tema escuro, #7fc3cf) só em links, foco e item ativo; o resto em cinzas quentes. Escalas do mapa sem mudança |
| V2 | Tipografia | Fonte do sistema (system-ui) em tudo | IBM Plex Sans no texto e IBM Plex Serif nos títulos, servidas de `web/fonts/` (woff2, cerca de 60 KB; licença OFL em `web/fonts/OFL.txt`). Números tabulares em tabelas, ficha, ranking, destaques e gráficos |
| V3 | Cantos | 8 a 14 px; botões e abas em pílula | 2 a 4 px |
| V4 | Abas (Mapa, Análise, Como calcular) | Botões arredondados, o ativo preenchido de roxo | Texto com sublinhado de 2 px na cor institucional no item ativo |
| V5 | Alternâncias (10 maiores/menores; Casos/Taxa) | Botões arredondados com fundo lilás no ativo | Mesmo padrão sublinhado das abas |
| V6 | Botões | Pílulas; o principal em roxo | Retângulos com borda fina (contraste ≥ 3:1); o principal em cinza-escuro sólido |
| V7 | Sombras | No título e na legenda do mapa, na ficha, no tour e nos avisos | Nenhuma; borda fina só onde algo flutua sobre o mapa |
| V8 | Cartões | Análise e Como calcular em cartões com borda e fundo; indicadores da ficha em caixas | Seções separadas por linha fina e espaço; indicadores da ficha em linhas |
| V9 | Faixas coloridas à esquerda | Resultados da Análise (roxo), frase-resumo da ficha (azul/vermelho), tela de erro | Removidas; a hierarquia vem do tamanho e do peso do texto |
| V10 | Topo | Título e subtítulo; faixa amarela de aviso em toda a largura | Cabeçalho de relatório: título em serifa, subtítulo com período e fontes, nota discreta sob o título e crédito "TCC · Sistemas de Informação · UFPB/CCAE" à direita |
| V11 | Números-resumo da Análise | Quatro cartões com número de 28 px | Linha de destaques entre filetes, número de 20 px e rótulo curto |
| V12 | Principais resultados | Título em negrito, evidência e pergunta em itálico roxo | Um parágrafo por resultado com os números em negrito; "Para a gestão: …" em texto normal |
| V13 | Tela Sobre | Avisos numa caixa amarela | Seções com títulos discretos em versalete: Como usar, Indicadores, Como ler, Fontes |
| V14 | Favicon | Roxo | Azul-petróleo |

### Texto (antes → depois)

| # | Onde | Antes | Depois |
|---|---|---|---|
| T1 | Ranking | "Bom Jesus — 505,5 por 100 mil/ano" (travessão) | "Bom Jesus: 505,5 por 100 mil/ano" |
| T2 | Aviso de notificação | Faixa amarela no topo; "Notificação não é ocorrência" no Sobre; "A notificação mede o registro, não a ocorrência" em Fontes e limitações | Uma nota sob o título: "Os números são casos notificados pelos serviços de saúde, não o total de casos que ocorrem." Em Como calcular fica só a leitura específica do observado ÷ esperado |
| T3 | Aviso de poucos casos | Na legenda do mapa, no ranking, na tabela, três vezes na ficha, no Sobre e três vezes em Como calcular | Só onde há asterisco ou valor instável: nota do ranking e das tabelas ("* Menos de 10 casos no período: valor instável."), aviso curto na ficha e uma linha "Como ler" no Sobre. Saiu da legenda, da frase-resumo e dos "Cuidado" de taxa e de local |
| T4 | Resultados (Análise) | "…não só a mulher adulta."; "…mas não só pelo tamanho."; "…ou seja, notifica proporcionalmente mais…"; "É onde vale o gestor investigar primeiro."; "Vale conhecer o que funciona neles." | Frases diretas, sem essas construções: "Meninas e mulheres jovens concentram os casos."; "Os casos se concentram nos municípios maiores."; dois títulos passaram a trazer o número calculado ("17 municípios notificam menos da metade do esperado.") |
| T5 | Título do bloco | "Leituras prontas"; "Pergunta para a gestão:" | "Principais resultados"; "Para a gestão:" |
| T6 | Destaques | "casos por 100 mil mulheres por ano (média do estado)"; "variação de casos entre 2019 e 2024" | "por 100 mil mulheres por ano, estado"; "variação dos casos, 2019 a 2024" |
| T7 | Sobre | "Mostra as notificações … para apoiar gestoras e gestores públicos a planejar a rede de atendimento."; "Escolha o que ver no topo à esquerda: …"; "Começar pelo tour" | "Notificações de violência contra a mulher nos 223 municípios da Paraíba, de 2019 a 2024. Feito para gestoras e gestores da rede de atendimento."; um passo por frase; "Ver o tour" |
| T8 | Tour | "Agora o mapa compara cada município…"; "dá para comparar idades…"; "qualquer número do painel pode ser refeito…" | "Cada município comparado com o estado. Azul: abaixo do esperado. Vermelho: acima."; "A taxa por 100 mil mulheres da faixa permite comparar idades com populações diferentes."; "Todas as contas podem ser refeitas numa planilha." |
| T9 | Ficha | "Com números tão pequenos, um caso a mais ou a menos muda muito a taxa e o observado ÷ esperado."; "Barra: … · traço preto: …"; "Detalhe por faixa, em casos ou em taxa, em 'Faixa etária em detalhe'." | "Poucos casos (N no tipo e período): taxa e observado ÷ esperado instáveis."; "Barra: … Traço: …"; "Detalhe por faixa abaixo, em casos ou em taxa." |
| T10 | Dicas do indicador | "Quantidade de notificações. Mostra onde está o volume de atendimento."; "Compara o município com o estado: 1 é igual, abaixo de 1 notifica menos, acima notifica mais." | "Número de notificações. Mostra o volume de atendimento."; "Compara com o estado: 1 é igual; abaixo de 1, notifica menos; acima, mais." |
| T11 | Como calcular | "Os cinco indicadores deste painel … Nenhum modelo estatístico complexo é usado …"; definições longas; "Não é um sexto indicador: …" | "Como os indicadores são calculados" e uma frase de fontes; definições de uma linha ("Casos por ano a cada 100 mil mulheres do município."); "Contexto: local de atendimento", terminando em "Não é um indicador." |
| T12 | Rodapé | Crédito do TCC repetido | Crédito só no topo; rodapé com "Dados públicos e agregados, sem identificação de pessoas." e o endereço do código-fonte |

### Conferência

- Contraste mínimo (testar_usabilidade.py): claro 5,29:1 (antes 4,77:1); escuro 6,36:1 (antes 5,9:1). Foco na cor institucional: 8,8:1 (claro) e 9,2:1 (escuro). Paleta do mapa sem mudança (ΔE mínimo 10,0).
- Lighthouse (página inicial, servidor com compressão): celular Desempenho 99 e Acessibilidade 100; computador 100 e 100 (`docs/lighthouse/`). Sem pré-carregamento das fontes, o celular caía para 96. O pré-carregamento só é feito quando o painel é servido por http, porque no duplo clique (`file://`) o navegador o bloqueia e acusa erro de CORS.
- Testes: dados 66, painel 120 (Firefox e WebKit 119), usabilidade 30, nos dois modos de abertura. Novo teste: nenhum travessão nos textos das telas, do Sobre e do Tour.

## Melhorias cartográficas no mapa (20/11/2026)

Dados, SQL, fórmulas e indicadores não mudaram. O exportador passou a gravar no `dados.json` o contorno do estado e das 16 regiões de saúde, calculados no PostGIS pela união das geometrias municipais (`ST_Union`, simplificados a cerca de 250 m). São só desenho e não entram em nenhuma conta.

| # | Elemento | Antes | Depois | Princípio cartográfico |
|---|---|---|---|---|
| C1 | Casos notificados | Municípios coloridos por classe de casos (mapa coroplético de contagem) | Círculo no centroide de cada município, com **área** proporcional aos casos (raio pela raiz quadrada; o maior, João Pessoa, com 26 px), sobre base cinza com limites. Os maiores são desenhados atrás. Taxa e observado ÷ esperado continuam em cores | Contagens absolutas pedem símbolos proporcionais: no coroplético, município grande "pesa" pela área do território, não pelo número de casos. Raio pela raiz quadrada porque o olho compara áreas |
| C2 | Valor instável | Só um * no ranking e nas tabelas; no mapa, nada | Hachura leve (linhas diagonais de 1 px a cada 8 px) sobre a cor dos municípios com menos de 10 casos no tipo e período, com item próprio na legenda e contagem (95 no total de 2019 a 2024) | Sinalizar incerteza no próprio mapa, sem esconder o dado: a cor continua legível e a textura avisa que o valor oscila. A linha (escura ou clara) é a de maior contraste com a cor: mínimo de 3,22:1 nos dois temas |
| C3 | Contorno do estado | Igual aos limites municipais | Linha grossa (2,4 px) na cor do texto | Hierarquia de linhas: o limite mais importante é o mais grosso |
| C4 | Regiões de saúde | Sem limite visível | Linha intermediária (1,3 px, cinza) entre o estado e os municípios, com opção "Mostrar limites das regiões de saúde" | Hierarquia visual e unidade de gestão do SUS, que é a escala do planejamento regional |
| C5 | Cidades de referência | Nenhum rótulo | Rótulos de João Pessoa, Campina Grande, Patos, Sousa, Cajazeiras, Guarabira e Monteiro, em ordem de prioridade, sem sobrepor outro rótulo, a ficha, a legenda ou o título; o texto vai à esquerda do ponto quando à direita não cabe; os dois últimos somem com menos zoom. As sedes das 16 regiões não estão nos dados oficiais do DATASUS (os nomes são só "2ª Região" etc.), por isso entram só esses 7 polos | Pontos de referência para a pessoa se localizar; colocação de rótulos sem conflito |
| C6 | Escala e fonte | Ausentes | Barra de escala em km e "Fonte: SINAN/TABNET, 2019 a 2024; IBGE, Censo 2022 e malha municipal" no canto inferior esquerdo | Elementos obrigatórios de um mapa temático |
| C7 | Enquadramento com a ficha | Zoom no município escolhido; parte do estado ficava atrás da ficha | O recorte inteiro (estado ou região) é enquadrado na área livre: à esquerda da ficha no computador e acima dela no celular. Sem a ficha, a legenda também é descontada | Nenhum dado escondido por elemento da interface |
| C8 | Navegação | Arraste e zoom livres | Arraste limitado à Paraíba com margem (o limite é recalculado após cada enquadramento, para não puxar o mapa de volta), zoom mínimo e máximo e botão "Ver estado inteiro" | Evitar que a pessoa se perca num mapa vazio |
| C9 | Legenda | Classes com rótulo; média do estado só em texto | Título com unidade ("Taxa por 100 mil mulheres por ano"; "Casos notificados (número de notificações)"; "Observado ÷ esperado (1 = igual ao estado)"), recorte atual (tipo · período · Paraíba ou região), número de municípios em cada classe com mini-histograma, ◆ na classe da média do estado, item da hachura e uma linha explicando as classes (quintis na taxa; classes fixas em torno de 1 no observado ÷ esperado; área proporcional nos casos, com 3 círculos de referência: 10, 100 e 1.000) | A legenda diz o que se mede, em que unidade, como as classes foram feitas e quanto pesa cada uma |
| C10 | Filtro de região | Municípios de fora esmaecidos | Além disso, o limite da região escolhida é destacado (3,2 px, cor institucional) | Figura e fundo: a região em foco se destaca sem esconder o contexto |
| C11 | Baixar mapa (PNG) | Não havia | O mapa atual é redesenhado num canvas com título (indicador, tipo, período, recorte), legenda, barra de escala, rótulos e fonte, e baixado como PNG (em 2×). Funciona nos dois modos de abertura; se falhar, uma mensagem orienta a abrir pelo link publicado | Mapa pronto para relatório, com os elementos que o tornam legível fora do painel |
| C12 | Celular com a ficha aberta | Legenda, escala e fonte ficavam por cima da ficha | Enquanto a ficha está aberta, o celular esconde legenda, escala, fonte e "Ver estado inteiro"; a dica da região de saúde (que repete o rótulo) também sai, para o mapa continuar na primeira tela | No espaço pequeno, mostrar o dado e esconder o acessório |

Conferência:
- Testes novos: área dos círculos de João Pessoa, Campina Grande e Sousa proporcional aos casos (r² ÷ casos constante; maiores atrás); hachura exatamente nos 95 municípios com menos de 10 casos (igual à view) e contagem por classe somando 223; enquadramento com a ficha aberta no computador e no celular; PNG gerado nos dois modos de abertura; rótulos sem sobreposição; regiões ligam e desligam; limite da região escolhida destacado; contraste da hachura ≥ 3:1 nos dois temas.
- Testes: dados 67, painel 138 (Firefox e WebKit 137), usabilidade 32, 0 falhas.
- Lighthouse local (com compressão): celular 97 e 98 de desempenho (antes 99) e 100 de acessibilidade; computador 100 e 100. A primeira versão ficou em 95: o mapa era desenhado e logo reenquadrado na abertura. Calcular a vista antes de pôr as camadas e adiar contornos e rótulos para depois do primeiro desenho recuperou quase toda a diferença.

## Revisão visual a partir da auditoria do site publicado (20/11/2026)

Dados, SQL, fórmulas, indicadores e funções não mudaram.

### Princípios adotados

1. **Escala sequencial: claro = baixo, escuro = alto, sempre**, também no tema escuro. O leitor tende a ler a cor mais escura como "mais" (*dark-is-more bias*); inverter a escala no tema escuro faria o mesmo município parecer alto num tema e baixo no outro.
2. **Passos de claridade uniformes** entre classes vizinhas, para que a distância visual corresponda à distância entre classes.
3. **Escala divergente: extremos mais escuros, centro claro.** O centro é o valor de referência (O/E = 1, igual ao estado).
4. **Cor só onde carrega informação.** Gráficos em cinza neutro; uma única série ou barra destacada na cor institucional; linha de referência cinza e tracejada.

Referências:
- BREWER, C. A.; HARROWER, M. *ColorBrewer 2.0: color advice for cartography*. Penn State University. Disponível em: https://colorbrewer2.org. Paletas YlOrRd (sequencial) e PuOr (divergente), 5 classes, ambas marcadas como seguras para daltonismo.
- HARROWER, M.; BREWER, C. A. ColorBrewer.org: an online tool for selecting colour schemes for maps. *The Cartographic Journal*, v. 40, n. 1, p. 27–37, 2003.
- DATAWRAPPER ACADEMY. *Which color scale to use when visualizing data* e *What to consider when choosing colors for data visualization*. Disponível em: https://academy.datawrapper.de.
- SCHIEWE, J. Empirical studies on the visual perception of choropleth maps: the dark-is-more bias. *KN – Journal of Cartography and Geographic Information*, v. 74, p. 171–180, 2024.

### Itens (antes → depois)

| # | Elemento | Antes | Depois |
|---|---|---|---|
| R1 | Mapa e legenda no tema escuro | Na versão publicada, o fundo do mapa e da legenda ficavam claros no tema escuro | Fundo do mapa e da legenda seguem o tema (na versão em desenvolvimento já seguiam; agora um teste mede a luminância do fundo nos dois temas, em 1366 e no celular). As paletas são idênticas nos dois temas: claro continua sendo baixo |
| R2 | Cores da taxa | Rampa azul própria (#b7d3f6 a #104281), invertida no tema escuro: lá o azul mais escuro era o valor mais baixo | ColorBrewer YlOrRd 5: #ffffb2, #fecc5c, #fd8d3c, #f03b20, #bd0026, igual nos dois temas |
| R3 | Cores do observado ÷ esperado | Divergente azul–vermelho própria (#1c5cab a #c93b3a), centro bege (#d4cfc4) que no tema escuro virava cinza-escuro (#4a4944), mais escuro que os extremos | ColorBrewer PuOr 5: #5e3c99 (menos de 0,5), #b2abd2 (0,5 a 0,8), #f7f7f7 (0,8 a 1,25), #fdb863 (1,25 a 2), #e66101 (2 ou mais). O limite municipal continua visível sobre a classe central (#f7f7f7) |
| R4 | Classes da taxa | Quintis recalculados a cada combinação de tipo e período: a mesma cor mudava de significado ao trocar o filtro | Classes fixas por tipo, calculadas uma vez a partir das taxas anuais 2019–2024 de todos os municípios (quintis das taxas positivas, arredondados): total 40/60/90/140; física 30/50/70/120; psicológica 20/30/50/80; sexual 15/25/40/60. Linha na legenda: "Classes fixas: quintis das taxas anuais dos municípios de 2019 a 2024 neste tipo, arredondados. Valem para qualquer ano ou período." |
| R5 | Legenda com a ficha aberta | No canto inferior direito: com a ficha aberta (também à direita), ficava coberta por ela | Sempre visível no computador, no canto inferior esquerdo, também com a ficha aberta (o enquadramento desconta a largura da legenda e da ficha). No celular, recolhível pelo botão "Legenda" (aria-expanded); com a ficha aberta, continua escondida para o mapa caber na tela |
| R6 | Cores dos gráficos | Quatro cores genéricas (uma por tipo), sem hierarquia | Cinza neutro; uma série destacada em azul-petróleo (Sexual na série anual e no gráfico de tipos; a faixa com mais casos e a de maior taxa nos gráficos de faixa etária); linha do estado cinza e tracejada; nenhuma das 4 cores antigas |
| R7 | Hachura do valor instável | Linha a cada 8 px, sempre ligada | Hachura sutil (1 px a cada 10 px, opacidade mínima que dá contraste ≥ 3:1 com a cor de fundo) e opção "Destacar municípios com poucos casos", ligada por padrão; o item da legenda some quando desligada |
| R8 | Mini-histograma da legenda | Em todas as classes, inclusive nos quintis (onde as barras eram quase iguais por construção) | Só nas classes fixas do observado ÷ esperado; na taxa, só a contagem de municípios |
| R9 | Mapa de casos | Pontos das cidades de referência sobre os círculos; círculos na cor institucional | Sem os pontos (rótulos só com halo); círculos laranja-escuro (#d95f02) semitransparentes com contorno branco sobre base cinza clara |
| R10 | Limites das regiões | Mais finos e mais claros que o necessário para se distinguir dos municipais | Regiões em 1,8 px, cor quase preta (#34322e); municípios em 0,6 px, cinza translúcido. Hierarquia: estado > região > município |
| R11 | Botões do cabeçalho e do mapa | "Ver estado inteiro" como botão de texto grande; "Sobre o painel", "Tour" e "Copiar link" como botões com borda | "Ver estado inteiro" é um botão de ícone de 44 px junto ao zoom, com aria-label e title; os três do cabeçalho viraram links de texto sem borda |
| R12 | Rótulos da legenda | Rótulos longos repetindo a unidade em cada classe | Rótulos curtos ("menos de 40", "40 a 60", "2 ou mais"); o significado fica no título ("Observado ÷ esperado (1 = igual ao estado; abaixo de 1, notifica menos)") |
| R13 | Foco ao abrir a ficha | Foco no título com moldura visível | Foco programático no título (leitor de tela anuncia o município) sem moldura; o foco por Tab nos controles continua com contorno |
| R14 | Números nos gráficos e na tabela | Todos os valores em negrito; colunas numéricas largas | Valores em peso normal, só o número comentado em negrito; na tabela da Análise, colunas numéricas compactas e alinhadas à direita (largura máxima 820 px) |
| R15 | Daltonismo e escala de cinza | ΔE mínimo medido, sem conferir a ordem das classes | Conferidas a ordem de claridade (L*) e a diferença mínima entre vizinhas em visão normal, protanopia, deuteranopia, tritanopia e escala de cinza (números abaixo) |

### Conferência

- **Ordem preservada em todas as simulações e em cinza:** na sequencial, L* cai a cada classe; na divergente, forma um V com o centro mais claro.
- L* sequencial (normal e cinza): 98,4 · 84,5 · 69,7 · 53,8 · 39,5 (menor passo 13,9). Protanopia: menor passo 14,1; deuteranopia 11,5; tritanopia 9,9 (97,2 · 82,0 · 66,1 · 53,5 · 43,6).
- L* divergente (normal e cinza): 33,8 · 71,7 · 97,2 · 79,7 · 57,4 (menor passo 17,5; protanopia 21,1; deuteranopia 15,4; tritanopia 20,0).
- ΔE mínimo entre classes vizinhas (iguais nos dois temas): sequencial 24,5 (normal), 19,4 (protanopia), 13,1 (deuteranopia), 16,1 (tritanopia); divergente 33,3 / 26,5 / 23,6 / 25,6.
- Hachura: linha escura (#262522) com opacidade 0,5 a 0,75 nas classes claras; branca com 0,5 a 0,65 sobre #bd0026 e #5e3c99. Contraste linha × cor de 3,01 a 3,32:1 (mínimo exigido 3:1), conferido nos padrões do próprio mapa.
- Contagens da legenda (todos os tipos, 2019–2024): taxa 74 / 50 / 44 / 35 / 20, 95 com hachura; observado ÷ esperado 76 / 61 / 42 / 32 / 12.
- Testes: dados 67, painel 157 (Firefox e WebKit 156), usabilidade 34, 0 falhas. Novos: paletas e classes fixas (iguais em "todos os anos" e em 2024; diferentes por tipo); histograma só no O/E; legenda visível sem cobrir a ficha; foco no título sem moldura; fundo do mapa e da legenda conforme o tema; legenda recolhível no celular; gráficos com uma série destacada; rótulos dentro do mapa; ordem de claridade nas simulações.
- Lighthouse local (com compressão): celular 98 de desempenho no relatório guardado (quatro rodadas: 93, 97, 98 e 97; mediana 97,5; versão anterior 97 e 98), computador 100; acessibilidade 100 nos dois.
- Capturas novas em `capturas/`: `{1366,celular}_{claro,escuro}_mapa_{taxa,oe,casos}.png`, além de `*_mapa_ficha.png` (ficha aberta com a legenda) e `*_analise.png`.

## Revisão dos textos para leitura rápida por gestores (22/11/2026)

Dados, fórmulas, indicadores e funções não mudaram: só os textos da tela.

**Problema de partida.** A frase "Notifica bem mais que o estado: 4,64 do esperado" dava a entender que Sumé notifica mais que a Paraíba inteira. O número 4,64 compara Sumé com a **média** da Paraíba, levando em conta o número de mulheres do município.

**Regras adotadas**
1. A referência é sempre "a média da Paraíba", nunca "o estado" sozinho.
2. Toda comparação mostra os dois números lado a lado, com unidade.
3. Observado ÷ esperado em palavras. Acima de 1: "X vezes a média". Abaixo de 1: fração ou porcentagem simples ("cerca de 1/10", "62% do esperado"). O nome técnico só aparece em letra menor e no "Como calcular".
4. Nome do indicador na tela: "Comparação com a média da Paraíba".
5. Casos sempre inteiros. Taxas com no máximo 1 casa decimal. Porcentagens sem casas acima de 10%.
6. Legenda da comparação em palavras, com os limites numéricos em letra menor.
7. Frase-resumo da ficha calculada, nunca digitada.
8. Participação do município: "Tem X% das mulheres da Paraíba e Y% dos casos notificados."
9. Uma ideia por frase. Sem símbolos (÷, ×, ◆) em rótulos principais. Siglas explicadas na primeira vez.

**Como a comparação vira palavras** (`calculo.js`, funções de texto `faixaOE`, `oeCurto`, `casosAprox` e `resumo`)

| Índice | Faixa (legenda e cor) | Forma curta (ranking, etiqueta, ficha) | Frase-resumo |
|---|---|---|---|
| menos de 0,5 | muito abaixo da média (menos da metade) | menos de 0,075: "menos de 1/10 do esperado"; de 0,075 a 0,125: "cerca de 1/10 do esperado"; acima: "N% do esperado" | "X registra cerca de 1/10 (ou cerca de N%, arredondado à dezena) das notificações esperadas para o seu número de mulheres." |
| 0,5 a 0,8 | abaixo da média | "N% do esperado" | igual à linha anterior |
| 0,8 a 1,25 | perto da média | "N% do esperado" ou "X,X vezes a média" | "X registra notificações perto da média da Paraíba, considerando o número de mulheres." |
| 1,25 a 2 | acima da média | "X,X vezes a média" | "X registra X,X vezes mais notificações que a média da Paraíba, considerando o número de mulheres." |
| 2 ou mais | muito acima da média (mais do dobro) | "X,X vezes a média" | igual à linha anterior |

Toda frase-resumo termina com os dois números: "Se seguisse a média da Paraíba, teria cerca de N casos em 6 anos (ou em AAAA); registrou M." Com esperado abaixo de 0,5, o texto diz "menos de 1 caso". Sem nenhum caso: "X não registrou nenhuma notificação de 2019 a 2024."

**Frases geradas** (todos os tipos, 2019 a 2024)
- Sumé: "Sumé registra 4,6 vezes mais notificações que a média da Paraíba, considerando o número de mulheres. Se seguisse a média da Paraíba, teria cerca de 44 casos em 6 anos; registrou 205."
- Sousa: "Sousa registra cerca de 1/10 das notificações esperadas para o seu número de mulheres. Se seguisse a média da Paraíba, teria cerca de 175 casos em 6 anos; registrou 15."
- João Pessoa: "João Pessoa registra 1,4 vezes mais notificações que a média da Paraíba, considerando o número de mulheres. Se seguisse a média da Paraíba, teria cerca de 2.239 casos em 6 anos; registrou 3.049."

### Textos alterados (antes → depois)

| Onde | Antes | Depois |
|---|---|---|
| Cabeçalho, subtítulo | Notificações por município de residência, 2019 a 2024. Fontes: SINAN/TABNET (Ministério da Saúde) e Censo 2022 (IBGE). | Notificações por município onde a mulher mora, 2019 a 2024. Fontes: Ministério da Saúde (SINAN, o sistema de notificação) e IBGE (Censo 2022). |
| Filtro Indicador | Observado ÷ esperado | Comparação com a média da Paraíba |
| Dica do indicador (taxa) | Casos por ano a cada 100 mil mulheres. Compara municípios de tamanhos diferentes. | Casos por ano a cada 100 mil mulheres. Serve para comparar municípios de tamanhos diferentes. |
| Dica do indicador (comparação) | Compara com o estado: 1 é igual; abaixo de 1, notifica menos; acima, mais. | Mostra se o município notifica mais ou menos que a média da Paraíba, considerando o número de mulheres. |
| Filtro Região de saúde | Todo o estado | Toda a Paraíba |
| Dica da região | Recorta mapa, ranking e tabela. As cores mantêm a escala do estado. | Mostra só a região no mapa, no ranking e na tabela. As cores seguem a escala da Paraíba inteira. |
| Botões | Baixar mapa (PNG) · Baixar tabela (CSV) | Baixar mapa (imagem PNG) · Baixar tabela (CSV, abre no Excel) |
| Botão do mapa | Ver estado inteiro | Ver a Paraíba inteira |
| Título do mapa e da legenda | Observado ÷ esperado (1 = igual ao estado; abaixo de 1, notifica menos) | Comparação com a média da Paraíba, com "considerando o número de mulheres" logo abaixo |
| Legenda, classes da comparação | menos de 0,5 · 0,5 a 0,8 · 0,8 a 1,25 · 1,25 a 2 · 2 ou mais | muito abaixo da média (menos da metade) · abaixo da média · perto da média · acima da média · muito acima da média (mais do dobro), cada uma com o limite numérico em letra menor |
| Legenda, nota da comparação | ◆ Classe do estado (1). Números: municípios em cada classe. / Classes fixas em torno de 1 (igual ao estado). | Esperado: os casos que o município teria se notificasse como a média da Paraíba. Número à direita: municípios em cada faixa. / Os números menores são os limites de cada faixa (1 = igual à média). Nome técnico: observado ÷ esperado. |
| Legenda, taxa | ◆ ao lado da classe da média; "◆ Média do estado: 83,9. Números: municípios em cada classe." | "média da Paraíba" escrito sob a classe; "Média da Paraíba: 83,9 casos por 100 mil mulheres por ano. Número à direita: municípios em cada faixa." |
| Legenda, faixas da taxa | Classes fixas: quintis das taxas anuais dos municípios de 2019 a 2024 neste tipo, arredondados. Valem para qualquer ano ou período. | As faixas de cor são fixas e valem para qualquer ano ou período. Saíram das taxas anuais dos municípios de 2019 a 2024, divididas em 5 grupos de tamanho parecido e arredondadas. |
| Legenda, casos | Casos notificados (número de notificações). Área do círculo proporcional ao número de casos. Estado: 10.344 casos; 3 municípios sem caso. | Casos notificados. O tamanho do círculo segue o número de casos. Paraíba: 10.344 casos. 3 municípios sem nenhum caso. |
| Ranking e etiqueta do mapa (comparação) | Sumé: 4,64× o esperado · Sousa: 0,09× o esperado | Sumé: 4,6 vezes a média (4,64) · Sousa: cerca de 1/10 do esperado (0,09). O índice fica em letra menor e desempata. |
| Nota do ranking | Inclui só municípios com pelo menos 10 casos no tipo e período. | Só municípios com pelo menos 10 casos neste tipo e período. Na comparação, antes vem: "Comparação com a média da Paraíba, considerando o número de mulheres." |
| Tabelas (mapa e Análise), coluna | Observado ÷ esperado · Taxa por 100 mil/ano | Comparação com a média (1 = igual) · Taxa por 100 mil mulheres/ano |
| Rodapé da tabela da Análise | * menos de 10 casos em 6 anos: taxa e observado ÷ esperado instáveis. | * Menos de 10 casos em 6 anos: taxa e comparação com a média instáveis. |
| Ficha, frase-resumo | **Notifica bem mais que o estado:** 4,64 do esperado (todos os tipos, 2019 a 2024). | **Sumé registra 4,6 vezes mais notificações que a média da Paraíba, considerando o número de mulheres.** Se seguisse a média da Paraíba, teria cerca de 44 casos em 6 anos; registrou 205. |
| Ficha, aviso de poucos casos | Poucos casos (4 no tipo e período): taxa e observado ÷ esperado instáveis. | Poucos casos (4 neste tipo e período). Um caso a mais ou a menos muda muito a taxa e a comparação. |
| Ficha, casos | Estado: 10.344 (0,1% do estado; 1,7% das mulheres) | Paraíba: 10.344 casos. Tem 1,7% das mulheres da Paraíba e 0,1% dos casos notificados. |
| Ficha, taxa | 7,2 · Média do estado: 83,9 | 7,2 · casos por 100 mil mulheres por ano, contra 83,9 na média da Paraíba. Média da região de saúde (10ª Região): 13,5. |
| Ficha, comparação | Observado ÷ esperado · 0,09 · Esperado se seguisse o estado: 175,2 casos · Notifica menos que a média do estado (estado = 1) | Comparação com a média da Paraíba · **cerca de 1/10 do esperado** · Muito abaixo da média (menos da metade), considerando o número de mulheres. Esperado se seguisse a média da Paraíba: cerca de 175 casos. Registrou 15. · em letra menor: Índice: 0,09 (1 = igual à média). Nome técnico: observado ÷ esperado. |
| Ficha, tipos e faixa (traço) | Barra: % do município. Traço: % do estado. · dica "Estado: 50%" | Barra: % do município. Traço: % da Paraíba. · dica "Paraíba: 50%" |
| Ficha, faixa em taxa | Traço: taxa do estado na mesma faixa (por 100 mil mulheres da faixa, por ano). | Traço: taxa da Paraíba na mesma faixa. Casos por ano a cada 100 mil mulheres da faixa. |
| Ficha, local de atendimento | Mesma região: 9 casos (60,0%) · Poucos casos (N): porcentagens instáveis. · …referência regional; o dado não diz o motivo. | Mesma região: 9 casos (60%) · Poucos casos (N). As porcentagens mudam muito com um caso. · …referência regional. O dado não diz o motivo. |
| Ficha, serviços | Serviços declarados pelo município (MUNIC 2023, IBGE) · …em 2023; serviços criados depois não aparecem. | Serviços declarados pela prefeitura (pesquisa MUNIC 2023, do IBGE) · …em 2023. Serviços criados depois não aparecem. |
| Comparar municípios | A última coluna é a média do estado. · Estado (referência) · Casos esperados se seguisse o estado: 175,2 · Observado ÷ esperado · porcentagens com 1 casa | A última coluna mostra a Paraíba inteira, para comparar. · Paraíba (referência) · Casos esperados se seguisse a média da Paraíba: 175 · Comparação com a média da Paraíba (1 = igual) + linha nova "Em palavras" (ex.: "cerca de 1/10 do esperado") · porcentagens sem casas acima de 10% |
| Análise, número do topo | 83,9 por 100 mil mulheres por ano, estado | 83,9 casos por 100 mil mulheres por ano, média da Paraíba |
| Análise, resultado 4 | João Pessoa tem 29,5% dos casos e 21,6% das mulheres do estado (observado ÷ esperado: 1,36). | João Pessoa tem 22% das mulheres da Paraíba e 29% dos casos notificados. Registra 1,4 vezes mais notificações que a média da Paraíba, considerando o número de mulheres. |
| Análise, resultado 5 | N municípios notificam menos da metade do esperado. … O menor valor é o de Sousa (0,09). | N municípios registram menos da metade das notificações esperadas para o seu número de mulheres. … O menor valor é o de Sousa: cerca de 1/10 do esperado. Teria cerca de 175 casos se seguisse a média da Paraíba; registrou 15. |
| Análise, resultado 6 | N municípios notificam o dobro ou mais do esperado. … têm observado ÷ esperado de 2 ou mais. | N municípios registram o dobro ou mais das notificações esperadas para o seu número de mulheres. … registram 2 vezes ou mais a média da Paraíba, considerando o número de mulheres. |
| Análise, resultado 7 | …um único caso muda muito a taxa e o observado ÷ esperado. | …um único caso muda muito a taxa e a comparação com a média. |
| Análise, local | 91,2% foram atendidas na própria região de saúde, 7,6% em outra região da Paraíba e 1,2% fora do estado (122 casos). | Das mulheres notificadas, 91% foram atendidas na própria região de saúde, 7,6% em outra região da Paraíba e 1,2% fora da Paraíba (122 casos). |
| Análise, MUNIC | Na MUNIC 2023, o serviço mais declarado é… | Na MUNIC 2023, pesquisa do IBGE com as prefeituras, o serviço mais declarado é… |
| Análise, faixa etária | (25,1%) · Linha tracejada: taxa geral do estado · rótulo "estado: 83,9 por 100 mil/ano" | (25%) · Linha tracejada: taxa geral da Paraíba · rótulo "Paraíba: 83,9 por 100 mil/ano" |
| Análise, descrições | Local da notificação em relação à região de saúde de residência. · Casos e taxa anual por 100 mil mulheres. | Lugar da notificação comparado com a região de saúde onde a mulher mora. · Casos e taxa por 100 mil mulheres por ano. |
| Sobre o painel | Casos notificados: fichas do SINAN de mulheres residentes no município. · Observado ÷ esperado: casos do município em relação ao esperado pela média do estado (1 = igual). · Valores marcados com * vêm de menos de 10 casos e são instáveis. · Fontes com siglas (SINAN/TABNET, DATASUS, MUNIC) | Casos notificados: fichas de notificação de mulheres que moram no município. · Comparação com a média da Paraíba: mostra se o município notifica mais ou menos que a média, considerando o número de mulheres. Nome técnico: observado ÷ esperado. · Valores marcados com * vêm de menos de 10 casos. Um caso a mais ou a menos muda muito o valor. · Fontes com cada sigla explicada na primeira vez |
| Tour, passo 2 | Observado ÷ esperado: cada município comparado com o estado. Azul: abaixo do esperado. Vermelho: acima. | Comparação com a média da Paraíba: mostra se cada município notifica mais ou menos que a média da Paraíba, considerando o número de mulheres. Roxo: abaixo da média. Laranja: acima. (As cores antigas não valiam mais desde a paleta PuOr.) |
| Tour, passos 3 a 5 | …comparados com o estado… · O traço marca o estado. · Principais resultados do estado… | …cada um ao lado da média da Paraíba… · O traço marca a média da Paraíba. · Principais resultados da Paraíba… |
| Tour, dica | Setas ← → mudam de passo · Esc sai | As setas do teclado mudam de passo. Esc sai. |
| Como calcular, casos | Fichas de notificação do SINAN… · Contagem do TABNET… | SINAN e TABNET explicados na primeira vez (sistema de notificação do Ministério da Saúde; ferramenta de consulta pública). |
| Como calcular, comparação | Título "Observado ÷ esperado"; "Compara o município com o estado."; esperado = mulheres × (casos do estado ÷ mulheres do estado); "esperado 175,2 casos" | Título "Comparação com a média da Paraíba"; o que é, em palavras, com o nome técnico; fórmula com "Paraíba"; exemplo "esperado = 34.824 × (10.344 ÷ 2.055.832) = 175,2, ou seja, cerca de 175 casos. Registrou 15. 15 ÷ 175,2 = 0,09: cerca de 1/10 do esperado (8,6%)." |
| Como calcular, taxa, tipos, faixa, local, fontes | "Estado: 83,9" · "Estado: física…" · "SIDRA 9514" · "60,0%"; "fora do estado" | "Média da Paraíba: 83,9" · "Paraíba: física…" · "tabela 9514 do SIDRA, o banco de tabelas do IBGE" · "60%"; "fora da Paraíba"; IBGE, MUNIC e DATASUS explicados |
| Baixar mapa (PNG) | Média do estado: 83,9 por 100 mil/ano. Classes por quintis. (texto antigo, de antes das faixas fixas) · Classes fixas em torno de 1 (igual ao estado). | Média da Paraíba: 83,9 casos por 100 mil mulheres por ano. Faixas fixas para qualquer período. · Limites das faixas: 0,5 · 0,8 · 1,25 · 2 (1 = igual à média). Nome técnico: observado ÷ esperado. |

Ficaram como estavam, porque são dados para planilha e não texto de leitura: os nomes das colunas do CSV (`observado_sobre_esperado` etc.) e a mensagem técnica de erro de carga, que fala com quem instala o painel.

### Conferência
- Teste novo (`testar_front.py`): gera a frase-resumo para os 223 municípios × 4 tipos × 7 períodos (6.244 frases) e confere que nenhuma tem "que o estado", "do estado", "do esperado" sem complemento ou número de casos com casa decimal, que todas começam pelo nome do município e citam a Paraíba. Também confere as frases exatas de Sousa e Sumé e a de um município "perto da média".
- Legenda da comparação em palavras, com os limites em letra menor; marca "média da Paraíba" na classe certa da taxa; ficha de Sousa com "contra 83,9 na média da Paraíba" e "Muito abaixo da média"; comparação de municípios igual à view.
- Testes: dados 67, painel 159 (Firefox e WebKit 158), usabilidade 34, 0 falhas. Material do teste com usuários (`docs/teste_usuarios/`) regerado com os nomes novos.
- Capturas: `capturas/ficha_resumo_sume.png`, `ficha_resumo_sousa.png`, `ficha_resumo_joao_pessoa.png`.

## Layout do mapa: legenda compacta, canvas claro e mapa maior (22/11/2026)

Dados, fórmulas, indicadores e textos aprovados não mudaram: os textos só foram reorganizados.

| # | Elemento | Antes | Depois | Por quê |
|---|---|---|---|---|
| L1 | Legenda | Com os rótulos em palavras, cada classe ocupava 2 ou 3 linhas. A legenda rolava, cobria parte do mapa e escondia o botão de diminuir o zoom | Uma linha por classe: cor, rótulo em palavras e limite em letra menor na mesma linha, e o número de municípios à direita. Explicações ("Esperado: …", como as faixas foram feitas, média da Paraíba, "O tamanho do círculo…") dentro de **"Como ler esta legenda"**, recolhido. O título da legenda é o próprio botão de recolher a legenda inteira (aria-expanded; com "Legenda:" para leitor de tela), no computador e no celular | Sem rolagem em 1366×768, nas três telas do indicador. As explicações continuam a um clique |
| L2 | Legenda × mapa | A legenda podia ficar sobre os botões de zoom e sobre o estado | Altura máxima abaixo dos botões. Ao abrir ou recolher a legenda ou o "Como ler", trocar o indicador ou ligar e desligar a hachura, o mapa se reenquadra para nada ficar sobre o estado. Isso só acontece enquanto a pessoa não tiver arrastado ou dado zoom | Nunca esconder dado nem controle |
| L3 | Fundo do mapa no tema escuro | O mapa e a legenda seguiam o tema e ficavam escuros (item R1 da revisão visual) | **Canvas claro:** no tema escuro, o mapa e o que fica sobre ele (legenda, escala, fonte, botões, rótulos) e o título do mapa usam os tons do tema claro. Só a interface ao redor (filtros, ficha, ranking, abas) fica escura. As cores do desenho e do PNG passam a ser lidas do próprio mapa (`cssM` em `mapa.js`); a ficha continua lendo as do tema | Visto no site publicado: com fundo escuro, o quase branco de "perto da média" e o amarelo-claro das taxas baixas eram o que mais brilhava, o que invertia a leitura "escuro = mais" (Schiewe, 2024). Isto substitui o item R1 |
| L4 | Enquadramento com a ficha aberta | Margens fixas pela caixa do estado: com a legenda ao lado, a Paraíba ficava com 361 px de largura em 1366×768 | São testadas duas margens seguras, com o estado ao lado da legenda ou acima dela. Depois, uma grade de 7×7 margens menores, aceitas quando o **contorno real** do estado (não a caixa) não encosta na legenda nem nos botões de zoom. A legenda pode, assim, ocupar o canto vazio da caixa (o sudoeste, abaixo do Sertão). Vale o mesmo para uma região de saúde (contorno da região). Também foi refinado o passo de zoom (0,25 → 0,1). No celular, quando a legenda aberta deixaria menos de 120 px livres, o estado fica inteiro e a legenda por cima dele, recolhível | Mapa maior, sem nada sobre o estado |

### Conferência
- 1366×768, com a ficha de Sumé aberta, nos temas claro e escuro: a Paraíba tem **512 px** de largura, contra 361 px antes. Isso é **127%** da largura útil entre a legenda e a ficha (402 px; a meta era 60%). O contorno não toca a legenda, a ficha, os botões de zoom nem o título. O teste confere 600 pontos da linha desenhada e se os cantos e o centro de cada retângulo estão fora do estado (`isPointInFill`).
- Legenda em 1366×768 (taxa e comparação com a média, nos dois temas): sem rolagem vertical nem horizontal, todas as linhas com 18 px, "Como ler" recolhido, sem cobrir os botões de zoom nem o estado. O botão recolhe e mostra a legenda. Aberto o "Como ler", o mapa se reenquadra sem nada sobre o estado.
- Canvas claro: luminância do fundo do mapa 0,86 e da legenda 0,96 nos dois temas, enquanto o fundo da página fica em 0,01 no tema escuro. O teste antigo ("o fundo segue o tema") foi trocado por este.
- Celular (390×844): legenda recolhida por padrão (mostra só o título); aberta, o estado continua inteiro no mapa.
- Testes: dados 67, painel 169 (Firefox e WebKit 168), usabilidade 34, 0 falhas.
- Lighthouse local com compressão: celular 98, 97 e 96 em três rodadas (mediana 97; antes, mediana 97,5), relatório guardado 98. Computador 100. Acessibilidade 100 nos dois.
- Capturas: `capturas/{1366,celular}_{claro,escuro}_ficha_sume.png`, além das telas de taxa, comparação e casos já existentes.
