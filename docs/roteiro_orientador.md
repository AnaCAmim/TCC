# Roteiro da reunião com o orientador

Painel de indicadores de violência contra a mulher na Paraíba. Versão do ramo `bases-contexto`, antes do merge.

**Antes de começar**
- Abra o link publicado numa **janela anônima**, para a tela "Sobre o painel" aparecer como na primeira visita.
- Plano B, se a internet falhar: dê duplo clique em `web/index.html`; funciona sem internet.
- Deixe aberta a página do ramo para mostrar o código e os testes: https://github.com/AnaCAmim/TCC/tree/bases-contexto.

---

## 1. Demonstração em 5 minutos (seguindo o botão "Tour")

| Tempo | Tela | O que mostrar | Fala curta |
|---|---|---|---|
| 0:00 | Sobre o painel | A tela que abre sozinha na primeira visita | "O painel é para gestoras e gestores públicos. Esta tela diz para que serve, como usar em 3 passos, as fontes e os dois avisos: notificação não é ocorrência, e poucos casos dão valor instável." Clique em **Começar pelo tour**. |
| 0:40 | Passo 1 · Mapa da taxa | Mapa e legenda | "Cada município pintado pela taxa de notificação por 100 mil mulheres por ano. A média do estado é 83,9." |
| 1:20 | Passo 2 · Observado ÷ esperado | Mapa azul e vermelho; ranking "10 menores" | "Aqui cada município é comparado com o estado: 1 é igual, azul notifica menos, vermelho notifica mais. Os 10 menores só entram com pelo menos 10 casos, para não destacar acaso." |
| 2:00 | Passo 3 · Ficha de Sousa | Frase-resumo no topo | "A ficha diz primeiro o que olhar: Sousa notifica bem menos que o estado, 0,09 do esperado. Depois vêm os 5 indicadores, sempre ao lado do estado e da região de saúde." |
| 2:50 | Passo 4 · Faixa etária em taxa | Botões "Casos \| Taxa" | "Em casos, a faixa mais atingida no estado é 20 a 29 anos; em taxa, é 10 a 14 anos, 157,9 por 100 mil por ano. Por isso as duas formas." |
| 3:30 | Passo 5 · Análise | Leituras prontas | "Cada leitura é calculada dos dados e traz a pergunta que ela abre para a gestão. Por exemplo: 91,2% das mulheres foram atendidas na própria região de saúde." |
| 4:10 | Passo 6 · Como calcular | Fórmulas com exemplo real | "Toda conta pode ser refeita numa planilha. Esta é a regra que o senhor deu: só entra o que eu sei explicar." |
| 4:40 | Ficha → Imprimir / Baixar tabela (CSV) | Folha impressa ou CSV | "E dá para levar os dados para uma reunião: ficha impressa ou a tabela dos 223 municípios no Excel." |

---

## 2. Evidências de qualidade

| O quê | Resultado |
|---|---|
| Testes automáticos (rodam no `atualizar.bat`) | Dados: 66 verificações. Painel: 119. Usabilidade: 30. **0 falhas.** |
| Conferência tela × banco | Taxa e observado ÷ esperado do painel iguais às views SQL em **6.244** combinações de município × tipo × período; taxa por faixa em **2.230**; taxa das 16 regiões em **448**; local de atendimento em **669**; CSV dos 223 municípios igual à view. |
| Cargas que se protegem | A carga aborta e mantém o banco anterior se algum total não bater: 10.344 casos, 223 municípios e 2.055.832 mulheres (também por faixa etária). Simulações de erro confirmaram o aborto. |
| Navegadores | Chrome, Firefox e WebKit (motor do Safari): 0 falhas. |
| Lighthouse (página inicial) | Medido localmente com compressão: celular 99 de desempenho, 100 de acessibilidade, 100 de boas práticas e 100 de SEO; computador 100 em tudo. Relatórios em `docs/lighthouse/` e, no link publicado, em `docs/lighthouse/publicado/`. |
| Usabilidade e acessibilidade | Revisão pelas 10 heurísticas de Nielsen e pela WCAG 2.1 AA: 16 problemas na revisão e 11 ajustes de acabamento, com gravidade e correção (`docs/websig_usabilidade.md`). Contraste AA nos temas claro e escuro, paleta testada para daltonismo, uso completo pelo teclado (inclusive no mapa), celular. |
| Teste-piloto das tarefas | As 5 tarefas do teste com usuários levam 1 ou 2 ações a partir da página inicial. A primeira visita soma 1 clique (fechar o "Sobre"), só uma vez. |
| Código aberto | Repositório público com licença MIT; fontes e datas de cada dado em `dados/brutos/FONTES.md`. |

---

## 3. Decisões que preciso do senhor

1. **Merge do ramo `bases-contexto` na versão principal.** Ele acrescenta a faixa etária em taxa, os serviços da MUNIC 2023 e o local de atendimento, sem indicador novo, além do acabamento de interface. Posso fazer o merge?
2. **Teste com usuários e Comitê de Ética.** O material está pronto: roteiro de 20 min, tarefas com gabarito, SUS na versão brasileira validada, termo de consentimento e planilha. Fazemos o teste com 5 gestores antes da banca? Precisa de submissão ao CEP ou basta o termo?
3. **Título sem nudges.** O título do pré-projeto fala em nudges, que saíram do trabalho. Proposta: "Painel de indicadores de violência contra a mulher na Paraíba para apoio à gestão pública: desenvolvimento de um WebSIG". Mudo o título?
4. **Prazo do texto para a banca.** Até quando o senhor precisa do artigo tecnológico completo para revisar, e quando ele vai para a banca?

---

## 4. Perguntas prováveis, com resposta curta

| Pergunta | Resposta |
|---|---|
| Notificar menos quer dizer ter menos violência? | Não. O painel mede notificação, não ocorrência; isso está no aviso do topo, no "Sobre" e em cada leitura. Notificar pouco pode ser falta de acesso ou de registro. |
| Por que observado ÷ esperado, se já existe a taxa? | A taxa mostra o nível; o observado ÷ esperado diz quanto o município se afasta do estado (1 = igual). É a mesma informação em linguagem de "acima ou abaixo da média", que o gestor entende rápido. |
| Por que o corte de 10 casos? | Abaixo disso, um caso a mais ou a menos muda muito a taxa. O painel não esconde esses municípios: marca com * e avisa "valor instável". |
| O denominador de 2022 vale para 2019 a 2024? | É uma limitação declarada: o Censo 2022 é a única contagem municipal de mulheres por idade. Está em "Limitações" e em "Como calcular". |
| Como sei que os números do painel estão certos? | Três conferências: dados brutos, carga no banco (aborta se o total não bater) e exportação. Os testes comparam o painel com o banco em todas as combinações. |
| Por que os óbitos (SIM) não entraram? | Pela regra dos 5 indicadores. Além disso, são 482 óbitos em 6 anos, pouco demais por município. O levantamento está em `docs/bases_candidatas.md`. |
| E o Ligue 180 e as medidas protetivas? | O Ligue 180 não tem dado aberto por município. As medidas protetivas vêm por comarca, que reúne vários municípios. Ficaram registradas como bases não usadas, com o motivo. |
| Por que os tipos de violência não somam o total? | Uma notificação pode marcar mais de um tipo. O painel avisa isso nos tipos. |
| Os serviços da MUNIC são confiáveis? | São o que a prefeitura declarou em 2023. Por isso aparecem como contexto, com "sem dado" escrito por extenso e a nota de que serviços criados depois não aparecem. |
| O que são os 122 "fora da Paraíba"? | Mulheres que moram na Paraíba e foram notificadas em outro estado. Por isso a contagem por residência (10.344) é maior que por local de notificação (10.222). |
| Por que um mapa próprio e não o GeoNode? | O mapa próprio em Leaflet abre até sem internet, com duplo clique, e permite a ficha, o teclado e os testes. O GeoNode pode receber as camadas depois. |
| Como atualizar quando sair o SINAN de 2025? | Troca-se o arquivo bruto em `dados/brutos/`, registra-se a data no FONTES.md e roda-se o `atualizar.bat`: confere, carrega, exporta e testa. |
| Já testou com usuários de verdade? | Ainda não: depende da sua decisão sobre o Comitê de Ética (decisão 2). O teste-piloto automatizado e a revisão de usabilidade já estão feitos. |
