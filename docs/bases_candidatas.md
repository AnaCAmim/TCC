# Bases candidatas para o painel: levantamento (18/11/2026)

Levantamento feito **sem mudar nada no painel**. Atualização de 18/11/2026: a seção 1 (faixa etária) e a seção 3 (rede, MUNIC 2023) foram implementadas no painel; a seção 2 (residência × notificação) também foi implementada, no nível de região de saúde (ver a explicação dos 122 abaixo). Regra do projeto: só os 5 indicadores (casos, taxa por 100 mil mulheres por ano, tipos, faixa etária, observado ÷ esperado), tudo explicável e recalculável numa planilha. Toda base abaixo precisaria da aprovação do orientador antes de entrar.

Cada acesso foi testado em 18/11/2026, e as amostras estão em `dados/brutos/amostras/`, descritas em `dados/brutos/FONTES.md`. "Sem dado" quer dizer que a fonte não informa, e não que o serviço não existe.

---

## 1. População feminina por faixa etária e município (Censo 2022, SIDRA 9514)

| Item | Resultado |
|---|---|
| Fonte e link | IBGE, Censo 2022, SIDRA tabela 9514, API de agregados: `servicodados.ibge.gov.br/api/v3/agregados/9514` (variável 93, Sexo = Mulheres, classificação 287 = Idade) |
| Cobertura municipal | **Sim**: 223 municípios. A soma dá 2.055.832, o mesmo denominador do painel |
| Anos | 2022 (Censo). Um único ano, como o denominador atual |
| Formato e acesso | JSON pela API, sem cadastro; também há download na página do SIDRA |
| Licença | Dados públicos do IBGE, com citação da fonte. [VERIFICAR o termo de uso do IBGE] |
| Teste | OK. Os grupos de 5 anos foram somados nas 10 faixas do SINAN. "1 a 4" = "0 a 4" − "Menos de 1"; "60 e mais" = soma dos grupos de 60 em diante. Em cada município, as faixas somam o total |
| Como entraria | A faixa etária deixa de ser só contagem e ganha a taxa: "casos por ano a cada 100 mil meninas ou mulheres daquela idade". |
| Fórmula | taxa da faixa = casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6 (a mesma fórmula da taxa atual) |
| Exemplo (estado, 2019–2024) | 10 a 14 anos: 1.315 ÷ 138.805 × 100.000 ÷ 6 = **157,9**; 20 a 29 anos: **143,4**; 60 e mais: **20,0**. Na contagem, 20 a 29 é a faixa mais atingida; na taxa, é 10 a 14 |
| Situação | **Implementado no painel**: tabela `populacao_faixa`, views `vw_faixa_municipio` e `vw_faixa_estado`, alternância "Casos \| Taxa por 100 mil/ano" na ficha e na Análise |
| Riscos de interpretação | Por município, cada faixa tem poucos casos, então a taxa fica instável (vale o aviso de menos de 10 casos). As faixas do SINAN têm larguras diferentes. A faixa "Ignorada" (21 casos) fica sem denominador. O denominador é de 2022 para os 6 anos |

## 2. SINAN violência: município de residência × município de notificação

| Item | Resultado |
|---|---|
| Fonte e link | SINAN/TABNET, base `violepb.def` (`tabnet.datasus.gov.br/cgi/deftohtm.exe?sinannet/cnv/violepb.def`); microdados nacionais em `ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/VIOLBR19.dbc` … `VIOLBR24.dbc` |
| Cobertura municipal | **Parcial**. O TABNET só aceita município na *linha*: município × município não sai numa consulta só ("Tabela de conversão não encontrada"). O que funciona é residência (município) × **região de saúde de notificação**. O cruzamento município × município exige os microdados |
| Anos | 2019–2024 (o mesmo recorte do painel; 2023 e 2024 ainda podem ser revisados) |
| Formato e acesso | TABNET: formulário (POST), resposta em texto. Microdados: arquivos `.dbc` de 21 a 46 MB por ano, Brasil inteiro; precisam de um programa para descompactar (pacote não padrão do Python ou do R) |
| Licença | Dados públicos do Ministério da Saúde (LAI). [VERIFICAR licença formal; o TABNET não indica uma] |
| Teste | OK no nível de região. Amostra: 220 municípios, 10.222 notificações; **92,3% notificadas na própria região de saúde**. Faltam 122 em relação aos 10.344: são **residentes da PB notificadas em outro estado** (explicação abaixo) |
| Como entraria | Na ficha: "x% das notificações de mulheres deste município foram feitas em outra região de saúde" (mais tarde, "em outro município"). |
| Fórmula | % fora = notificações de residentes feitas fora do município (ou da região) ÷ total de notificações de residentes × 100 |
| Situação | **Implementado no painel** como contexto: tabela `notificacao_local` (mesma região de saúde / outra região da PB / fora da PB), views `vw_local_atendimento` e `vw_local_estado`, bloco "Onde as mulheres deste município foram atendidas" na ficha e na Análise. No estado: 9.436 (91,2%) na própria região, 786 (7,6%) em outra região da PB e 122 (1,2%) fora da PB, sobre os 10.344. Os 92,3% citados acima eram sobre os 10.222 notificados na PB |
| Riscos de interpretação | Notificar fora não quer dizer que falta serviço: pode ser hospital de referência, trabalho ou preferência. A `violepb` inclui as paraibanas notificadas em outros estados (são os 122), mas o TABNET não mostra o município de notificação delas. Pelo TABNET, o nível municipal exigiria 223 consultas; os microdados exigem uma ferramenta fora da planilha |

### Diferença de 122 notificações (investigada em 18/11/2026)

| Tabulação no TABNET (`violepb.def`; mesmos filtros: Sexo = Fem; Lesão autoprovocada ≠ Sim; 2019–2024) | Total | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| Linha = município de **residência** (base do painel) | 10.344 | 1.740 | 1.256 | 1.360 | 1.700 | 1.953 | 2.335 |
| Linha = município de **notificação** | 10.222 | 1.722 | 1.242 | 1.339 | 1.684 | 1.919 | 2.316 |
| Diferença | **122** | 18 | 14 | 21 | 16 | 34 | 19 |

- Os filtros são idênticos nas duas consultas, e a diferença aparece em todos os anos; logo, não vem de filtro.
- A tabulação por notificação tem 168 municípios, **todos da Paraíba** (código 25xxxx), sem linha de "ignorado". O total cruzado (residência × região de notificação) dá os mesmos 10.222.
- Conclusão: a base `violepb` reúne as notificações de **residentes da PB**. São 122 mulheres paraibanas (1,2%) **notificadas por serviços de outros estados**. Como a tabela de conversão do TABNET só lista municípios de notificação da PB, essas notificações somem quando se tabula pelo local de notificação. Elas contam no painel, que usa o município de residência.
- O mesmo raciocínio indica que não entram residentes de outros estados notificados na PB: a soma por notificação (10.222) não passa da soma cruzada.
- [VERIFICAR, opcional] o estado de notificação dessas 122 nos microdados `VIOLBR*.dbc` (campo do município de notificação com UF ≠ 25).
- Amostras: `dados/brutos/amostras/tabnet_sinan_notificacao_x_ano_2019-2024.txt` e `tabnet_sinan_residencia_x_regiao_notificacao_2019-2024.txt`.

## 3. Rede de atendimento à mulher

| Item | Resultado |
|---|---|
| Fonte e link | **IBGE, MUNIC 2023**, a edição mais recente com bloco "Política para Mulheres": `ftp.ibge.gov.br/Perfil_Municipios/2023/Base_de_Dados/Base_MUNIC_2023.xlsx`. A MUNIC 2024 não traz esse bloco. A 2018 traz, mas é mais antiga |
| Cobertura municipal | **Sim**: 223 municípios. É a prefeitura que responde |
| Anos | 2023 (MUNIC 2018 também tem o bloco, para comparação) |
| Formato e acesso | Planilha .xlsx/.ods de 23 MB, download direto. Não foi guardada no repositório; só a amostra da PB |
| Licença | Dados públicos do IBGE, com citação. [VERIFICAR o termo de uso] |
| Variáveis testadas (PB, 2023) | Organismo executivo de políticas para mulheres (MPPM01): 139 Sim. Plano municipal (MPPM11): 64 Sim. Conselho municipal (MPPM13): 107 Sim. Casa-abrigo ou acolhimento (MPPM20): 6 Sim. CEAM/NIAM, centro de referência (MPPM24a1): 27 Sim. Serviço especializado em violência sexual (MPPM24a2): 28 Sim. Delegacia especializada da mulher (MSEG168): 13 Sim, 158 Não, **52 sem dado**. Abrigo institucional do SUAS (MASS2514): 2 Sim |
| Juizado / vara | **Sem dado** na MUNIC 2023. O TJPB tem a página da Coordenadoria da Mulher (`tjpb.jus.br/coordenadoria-mulher/juizados`), mas ela recusou acesso automático (HTTP 403); conferir à mão |
| Fontes estaduais | SEMDH-PB, SESDS-PB e TJPB: **nenhuma lista oficial estruturada (CSV ou planilha) encontrada**. Notícias de jun/2025 citam 21 DEAMs em 19 municípios, mas é fonte secundária [VERIFICAR com a Coordenadoria das DEAMs]. Caminho: pedido via LAI à SESDS e à SEMDH |
| Como entraria | Na ficha, como contexto e não como indicador: "Serviços informados pela prefeitura em 2023: organismo de políticas para mulheres (sim/não/sem dado), centro de referência, casa-abrigo, delegacia da mulher". |
| Fórmula | Nenhuma (sim / não / sem dado) |
| Situação | **Implementado no painel**: tabela `rede_atendimento` (organismo, centro de referência, casa-abrigo, delegacia especializada; a MUNIC 2023 não pergunta sobre "sala" em delegacia comum) e bloco na ficha com ícone + texto |
| Riscos de interpretação | É autodeclaração da prefeitura e pode estar errada ou desatualizada. Um serviço regional que atende o município pode não constar. "Não" na MUNIC não prova ausência, e "-" deve aparecer como "sem dado". A DEAM é estadual, e a prefeitura pode não saber informar |

## 4. Óbitos de mulheres por agressão (SIM, CID-10 X85–Y09)

| Item | Resultado |
|---|---|
| Fonte e link | SIM/TABNET, `tabnet.datasus.gov.br/cgi/deftohtm.exe?sim/cnv/obt10pb.def` (Mortalidade – Paraíba), óbitos por residência, Grupo CID-10 "Agressões" |
| Cobertura municipal | **Sim**, por município de residência |
| Anos | 2019–2024, disponíveis no TABNET (o formulário já lista até 2026; os anos recentes podem ser preliminares [VERIFICAR]) |
| Formato e acesso | TABNET (POST); microdados no FTP do DATASUS |
| Licença | Dados públicos do Ministério da Saúde. [VERIFICAR licença formal] |
| Teste | OK: **482 óbitos** (72, 94, 83, 84, 79, 70 por ano), 4 deles em "município ignorado". Os 478 restantes batem com a extração anterior do projeto. Só 123 dos 223 municípios têm ao menos 1 óbito |
| Como entraria | — (ver riscos) |
| Fórmula | taxa de óbitos = óbitos ÷ mulheres × 100.000 ÷ 6 |
| Riscos de interpretação | **Fora da regra atual**: a decisão de 18/11/2026 tirou os óbitos do SIM do painel e do artigo. Os números são muito pequenos por município (quase todos abaixo de 10). Há possível má classificação (Y10–Y34, intenção indeterminada). "Agressão" não é sinônimo de feminicídio |

## 5. Estabelecimentos de saúde por município (CNES)

| Item | Resultado |
|---|---|
| Fonte e link | CNES/TABNET, `tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/estabpb.def` (Estabelecimentos por tipo – Paraíba); há também arquivos mensais no FTP do DATASUS |
| Cobertura municipal | **Sim**: 223 municípios |
| Anos | Mensal; o formulário oferece competências até out/2026. A amostra é de dez/2024 |
| Formato e acesso | TABNET (POST), texto |
| Licença | Dados públicos do Ministério da Saúde. [VERIFICAR licença formal] |
| Teste | OK: 8.503 estabelecimentos em dez/2024. Centro de saúde/UBS: 1.605, em 219 municípios. Hospital geral: 110, em 69. Unidade mista: 38, em 35. Pronto atendimento: 29, em 24 |
| Como entraria | Na ficha, como contexto: "Em dez/2024 o município tinha x UBS, y hospitais e z pronto atendimentos (CNES)". |
| Fórmula | Contagem, ou UBS por 10 mil mulheres = UBS ÷ mulheres × 10.000 |
| Riscos de interpretação | Contar estabelecimentos não mede capacidade, horário nem qualidade. O tipo "UPA" aparece como "Pronto atendimento". A competência escolhida muda os números. Não mostra se o serviço atende violência |

## 6. Ligue 180 e medidas protetivas (CNJ)

| Item | Resultado |
|---|---|
| Ligue 180 | Ministério das Mulheres: "Painel de Dados do Ligue 180" (Power BI, lançado em ago/2025) e "Painel da Rede". **Nenhum arquivo aberto por município foi encontrado.** O conjunto aberto do MDHC no dados.gov.br ("Ouvidoria Nacional de Direitos Humanos – ONDH", CC-BY, CSV trimestral desde 2020) é do **Disque 100**, não do Ligue 180. Caminho: pedido via LAI ao Ministério das Mulheres |
| Disque 100 (alternativa) | Tem as colunas `Município` (código IBGE) e `Município_da_vítima` (amostra do cabeçalho). Cada trimestre tem cerca de 940 MB, Brasil inteiro e todos os grupos vulneráveis. Risco: denúncia ≠ caso, uma denúncia pode ter várias violações, e o local da denúncia pode não ser o da vítima |
| Medidas protetivas | CNJ, "Painel da Violência Doméstica" (filtro por tribunal e ano desde 2020; painel interativo, não arquivo). API pública do **DataJud** (`api-publica.datajud.cnj.jus.br/api_publica_tjpb`, chave pública divulgada pelo CNJ): os dados vêm por processo, com órgão julgador (comarca). Teste de 18/11: **inconclusivo** (0 resultados na 1ª consulta, depois só sobrecarga, HTTP 429/504) |
| Cobertura municipal | Ligue 180: sem dado aberto. Medidas protetivas: **parcial**, por comarca (uma comarca atende vários municípios) |
| Como entraria | Não entraria agora. |
| Riscos de interpretação | Denúncias e processos medem a procura pelo serviço ou pela Justiça, não a violência. A comarca não é o município. As classes processuais variam entre tribunais |

---

## Recomendação (até 3 bases, todas dependendo do orientador)

1. **População feminina por faixa etária (SIDRA 9514).** É a mais forte. Não cria indicador novo: transforma a faixa etária (indicador 4) em taxa, com a mesma fórmula, mesma fonte e mesmo ano do denominador atual, e é recalculável numa planilha. A amostra já está conferida (soma 2.055.832). Mostraria, por exemplo, que a taxa mais alta é de 10 a 14 anos, embora 20 a 29 tenha mais casos.
2. **MUNIC 2023, rede de atendimento.** Como contexto na ficha (sim / não / sem dado), sem fórmula. Responde à pergunta do gestor "que serviço existe aqui?". Tem limite: é autodeclaração e não informa juizado.
3. **SINAN residência × região de notificação.** Mesma base do painel. Mostra onde as mulheres são notificadas (hoje, 92,3% na própria região de saúde). Começaria no nível de região, que o TABNET entrega; o nível municipal fica para depois, com os microdados.

Não recomendadas agora: SIM (excluído pela decisão de 18/11/2026; números pequenos), CNES (só contexto, sem relação direta com violência), Ligue 180 (sem dado aberto por município) e medidas protetivas (comarca ≠ município; acesso instável).
