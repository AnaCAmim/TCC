# Revisão de usabilidade e acessibilidade do painel, 18/11/2026 (atualizada na etapa 4)

Etapa 3. Revisão do painel pelas 10 heurísticas de Nielsen e pela WCAG 2.1 nível AA, antes do teste com usuários. Nenhum dado, SQL, fórmula ou indicador foi alterado; as mudanças são só de interface (`web/index.html`, `css/painel.css`, `js/mapa.js`, `js/app.js`). As versões anteriores do front ficam numa cópia local (`backup/`), fora do repositório.

Como foi feita: inspeção do código e das telas, mais medições automáticas com Playwright (`testes/testar_usabilidade.py`, dentro do `atualizar.bat`). Na etapa 4, os testes do painel e de usabilidade passaram também no Firefox e no WebKit, o motor do Safari (`testar_navegadores.bat`). Não houve teste com leitor de tela real (NVDA, VoiceOver) nem em Safari de verdade (Mac ou iPhone).

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
| 14 | A dica do mapa (nome e valor) só aparecia ao passar o mouse; no toque e no teclado não havia dica, e os municípios do mapa não recebiam foco. | WCAG 1.4.13 Conteúdo em foco ou passagem do mouse; 2.1.1 Teclado; H6 | 1 | **Corrigido na etapa 4.** Tab percorre os municípios do mapa em ordem alfabética (só os da região escolhida, se houver filtro); a mesma etiqueta "nome · valor" aparece acima do município, sem cobri-lo, com "Enter abre a ficha"; Enter ou espaço abre a ficha e Esc a fecha, devolvendo o foco ao município. No toque, o 1º toque mostra a etiqueta ("Toque de novo para abrir a ficha") e o 2º abre a ficha. Cada município tem `role=button` e rótulo "Nome: valor". Testado no Chrome, Firefox e WebKit. |
| 15 | No Safari (WebKit), o Tab pula links por padrão: o "Pular para o conteúdo", o ranking e os links "como calcular" ficavam fora do teclado. | WCAG 2.1.1 Teclado | 2 | `tabindex="0"` explícito nesses links (etapa 4). |
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

Nenhuma tarefa passou de 4 ações, por isso nenhuma precisou ser simplificada. As contagens já eram as mesmas antes desta etapa; o que mudou foi a T3, que agora se responde lendo uma frase em vez de comparar 11 barras (problema 3), e a busca, que avisa quando não acha o município (problema 1).

Limite do piloto: o robô sabe onde clicar. Ele mede o caminho mais curto, não se uma pessoa o encontra. Isso só o teste com usuários (`docs/teste_usuarios/`) mostra.

Registro: `capturas/piloto_tarefas.json` (gerado pelos testes) e capturas `piloto_T1.png` … `piloto_T4.png`, `piloto_celular_320.png`.

## Pendências

- Teste com leitor de tela real (NVDA no Windows) e em Safari de verdade (Mac ou iPhone); Firefox e WebKit já passam nos testes automáticos.
- Com o Tab, os 223 municípios do mapa vêm depois do ranking; quem não quiser percorrê-los pode usar a busca ou "Ver como tabela". Com filtro de região, só os municípios da região entram no Tab.
- Teste com 5 usuários do público-alvo (roteiro, tarefas, SUS e planilha em `docs/teste_usuarios/`). [CONFIRMAR COM ORIENTADOR] a necessidade de Comitê de Ética.
- Referências de apoio para o artigo [VERIFICAR]: NIELSEN, J. *Usability engineering*. Boston: Academic Press, 1993; W3C. *Web Content Accessibility Guidelines (WCAG) 2.1*. 2018; MACHADO, G. M.; OLIVEIRA, M. M.; FERNANDES, L. A. F. A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, v. 15, n. 6, p. 1291–1298, 2009.

## Compatibilidade entre navegadores (etapa 4)

| Navegador (Playwright) | testar_front.py | testar_usabilidade.py | Ajustes feitos |
|---|---|---|---|
| Chrome instalado | 85 OK, 0 falhas (inclui Copiar link) | 28 OK, 0 falhas | — |
| Firefox | 84 OK, 0 falhas | 28 OK, 0 falhas | Nenhum no painel. No teste: o 1º Esc fecha a lista de sugestões do campo (problema 16). O Firefox do Playwright não emula `is_mobile`; o celular foi testado com tela pequena e toque. |
| WebKit (motor do Safari) | 84 OK, 0 falhas | 28 OK, 0 falhas | Links com `tabindex="0"` (problema 15). No teste: o toque usa um ponto dentro do polígono, porque o centro da caixa pode cair no município vizinho. |

A leitura da área de transferência (Copiar link) e o PDF da ficha só são conferidos no Chrome, porque os outros navegadores do Playwright não liberam essas funções nos testes.

## Acabamento para a apresentação (ramo `bases-contexto`, 18/11/2026)

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
