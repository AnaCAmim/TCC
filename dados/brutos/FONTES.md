# Dados Brutos: Fontes e Datas de Acesso

| Arquivo | Fonte | Recorte | Acesso |
|---|---|---|---|
| `sinan_pb_mulheres_residencia_2019-2024_longo.csv` | SINAN/TABNET, Ministério da Saúde (base `violepb.def`) | Sexo = Feminino; município de **residência**; 2019 a 2024; casos por ano e tipo de violência. O total usado exclui a violência autoprovocada. | 14/10/2026 (data do arquivo) |
| `sinan_pb_mulheres_residencia_faixa_etaria_2019-2024.csv` | SINAN/TABNET (`violepb.def`) | Mesmo recorte; faixa etária; acumulado 2019 a 2024; Lesão autoprovocada ≠ Sim | 20/10/2026 |
| `ibge_populacao_feminina_2022.csv` | IBGE, Censo 2022, SIDRA tabela 9514 (variável 93, Sexo = Mulheres, Idade = Total), via API de agregados; nomes pela API de localidades | 223 municípios da Paraíba | 18/11/2026 |
| `ibge_sidra9514_mulheres_pb_2022.json`, `ibge_localidades_municipios_pb.json` | Respostas brutas das duas APIs do IBGE acima | — | 18/11/2026 |
| `datasus_base_territorial_jun26/` (rl_municip_regsaud.csv, tb_regsaud.txt, rl_regsaud_macsaud.csv, tb_macsaud.csv, rl_municip_macsaud.csv e os *_layout.txt) | Ministério da Saúde/DATASUS, **Base Territorial** (tabelas usadas pelo TABNET), arquivo `06-base_territorial_jun26.zip` de ftp://ftp.datasus.gov.br/territorio/tabelas/2026/ (SHA-256 do zip: f6e06a674cf7c83693df6a230b2068ea2e257c27970050ca320353e42688316a); documentação em ftp://ftp.datasus.gov.br/territorio/doc/bases_territoriais.pdf | Arquivos originais, sem edição (Brasil inteiro; a carga filtra a Paraíba). Município → região de saúde (16 na PB) → macrorregião (3). Os 223 municípios estão em exatamente uma região; as duas tabelas de macrorregião concordam | 18/11/2026 |
| `ibge_sidra9514_mulheres_idade_pb_2022.json` | IBGE, Censo 2022, SIDRA tabela 9514, API de agregados (variável 93, Sexo = Mulheres, grupos de 5 anos, "Menos de 1 ano" e Total) | 223 municípios; a carga soma os grupos nas 10 faixas do SINAN e confere 2.055.832 por município e no estado | 18/11/2026 |
| `ibge_munic2023_rede_atendimento_pb.csv` | IBGE, MUNIC 2023 (`ftp.ibge.gov.br/Perfil_Municipios/2023/Base_de_Dados/Base_MUNIC_2023.xlsx`), extraído por `pipeline/extrair_munic2023.py`: MPPM01 (organismo de políticas para mulheres), MPPM24a1 (CEAM/NIAM), MPPM20 (casa-abrigo ou acolhimento), MSEG168 (delegacia especializada no atendimento à mulher) | 223 municípios da PB; valores exatamente como na MUNIC ("Sim", "Não", "-" = sem dado) | 18/11/2026 |
| `sinan_pb_mulheres_residencia_x_regiao_notificacao_2019-2024.csv` | SINAN/TABNET `violepb.def` (linha = município de residência; colunas = as 16 regiões de saúde de notificação, 25001 a 25016; Sexo = Fem; Lesão autoprovocada ≠ Sim; 2019–2024). É a resposta do TABNET (em `amostras/`) sem as linhas vazias e o "&" final; valores intactos | 220 municípios com caso; soma 10.222 notificados na PB. Os 122 que faltam para 10.344 são residentes notificadas fora da PB (entram como "fora da Paraíba") | 18/11/2026 |
| `malha_municipal_pb_geojs.json` | Malha municipal da Paraíba: contornos derivados da malha municipal do IBGE, via repositório tbrugz/geodata-br (licença CC0 1.0, conferida em 18/11/2026) | 223 polígonos; a geometria de Cabedelo é corrigida na carga (`ST_MakeValid`) | 14/10/2026 |

Observações:
- O SINAN de 2023 e 2024 ainda pode ser revisado; uma nova extração pode mudar esses anos.
- O nome oficial vem do IBGE. A malha tem 3 nomes antigos (Santarém, Seridó, Campo de Santana); o IBGE usa Joca Claudino, São Vicente do Seridó e Tacima. O IBGE grafa "Quixaba", sem acento.
- Região de saúde: nomes oficiais do DATASUS sem o " - PB" (ex.: "1ª Região Mata Atlântica", "2ª Região"). A Base Territorial reflete a regionalização pactuada na Comissão Intergestores Bipartite da Paraíba (CIB-PB); ela não foi comparada, item a item, com a resolução estadual vigente.
- Totais conferidos: 10.344 notificações, 223 municípios, 2.055.832 mulheres. A população de cada município conferiu, uma a uma, com a de uma extração anterior do SIDRA feita no início do trabalho.

## Amostras do Levantamento de Bases (`amostras/`, 18/11/2026)

Só para testar o acesso; **nada disto entra no painel** (ver `docs/bases_candidatas.md`). O SIDRA por idade e a MUNIC 2023 saíram das amostras e viraram dados brutos do painel (tabela acima).

| Arquivo | Fonte e forma de acesso | Recorte | Acesso |
|---|---|---|---|
| `tabnet_sinan_notificacao_x_ano_2019-2024.txt` | SINAN/TABNET `violepb.def`, linha = município de notificação, coluna = ano, mesmos filtros | Soma 10.222 (122 a menos que por residência: notificadas fora da PB) | 18/11/2026 |
| `tabnet_sinan_residencia_x_regiao_notificacao_2019-2024.txt` | SINAN/TABNET `violepb.def`, POST em `tabcgi.exe` (linha = município de residência; coluna = região de saúde de notificação; Sexo = Fem; Lesão autoprovocada ≠ Sim; 2019–2024) | 220 municípios com caso; soma 10.222 (122 a menos que os 10.344: notificações sem região de notificação da PB) | 18/11/2026 |
| `tabnet_sim_obitos_mulheres_agressao_residencia_2019-2024.txt` | SIM/TABNET `obt10pb.def` (Mortalidade – Paraíba), óbitos por residência, Sexo = Fem, Grupo CID-10 = Agressões (X85–Y09) | 2019–2024; 482 óbitos (4 em "município ignorado") | 18/11/2026 |
| `tabnet_cnes_estabelecimentos_tipo_pb_dez2024.txt` | CNES/TABNET `estabpb.def` (Estabelecimentos por tipo – Paraíba), competência dez/2024 | 223 municípios; 8.503 estabelecimentos | 18/11/2026 |
| `mdhc_disque100_cabecalho_3tri2026.csv` | MDHC/ONDH, dados abertos do **Disque 100** (`dadosabertos.mdh.gov.br/disque100-terceiro-trimestre-2026.csv`, 940 MB, CC-BY; catálogo em dados.gov.br): só a linha de cabeçalho | Mostra as colunas `UF`, `Município` (código IBGE) e `Município_da_vítima` | 18/11/2026 |

Testes sem amostra: DataJud/CNJ (API pública `api-publica.datajud.cnj.jus.br/api_publica_tjpb`, chave pública divulgada pelo CNJ): em 18/11 respondeu 0 processos para a classe 1268 com filtro de data e depois só HTTP 429/504 (sobrecarga): **inconclusivo**. Ligue 180: só painel Power BI do Ministério das Mulheres; nenhum arquivo aberto encontrado. Página de juizados do TJPB: HTTP 403 para acesso automático.
