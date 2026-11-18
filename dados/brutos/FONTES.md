# Dados brutos: fontes e datas de acesso

| Arquivo | Fonte | Recorte | Acesso |
|---|---|---|---|
| `sinan_pb_mulheres_residencia_2019-2024_longo.csv` | SINAN/TABNET, Ministério da Saúde (base `violepb.def`) | Sexo = Feminino; município de **residência**; 2019 a 2024; casos por ano e tipo de violência. O total usado exclui a violência autoprovocada. | 14/10/2026 (data do arquivo) |
| `sinan_pb_mulheres_residencia_faixa_etaria_2019-2024.csv` | SINAN/TABNET (`violepb.def`) | Mesmo recorte; faixa etária; acumulado 2019 a 2024; Lesão autoprovocada ≠ Sim | 20/10/2026 |
| `ibge_populacao_feminina_2022.csv` | IBGE, Censo 2022, SIDRA tabela 9514 (variável 93, Sexo = Mulheres, Idade = Total), via API de agregados; nomes pela API de localidades | 223 municípios da Paraíba | 18/11/2026 |
| `ibge_sidra9514_mulheres_pb_2022.json`, `ibge_localidades_municipios_pb.json` | Respostas brutas das duas APIs do IBGE acima | — | 18/11/2026 |
| `datasus_base_territorial_jun26/` (rl_municip_regsaud.csv, tb_regsaud.txt, rl_regsaud_macsaud.csv, tb_macsaud.csv, rl_municip_macsaud.csv e os *_layout.txt) | Ministério da Saúde/DATASUS, **Base Territorial** (tabelas usadas pelo TABNET), arquivo `06-base_territorial_jun26.zip` de ftp://ftp.datasus.gov.br/territorio/tabelas/2026/ (SHA-256 do zip: f6e06a674cf7c83693df6a230b2068ea2e257c27970050ca320353e42688316a); documentação em ftp://ftp.datasus.gov.br/territorio/doc/bases_territoriais.pdf | Arquivos originais, sem edição (Brasil inteiro; a carga filtra a Paraíba). Município → região de saúde (16 na PB) → macrorregião (3). Os 223 municípios estão em exatamente uma região; as duas tabelas de macrorregião concordam | 18/11/2026 |
| `malha_municipal_pb_geojs.json` | Malha municipal da Paraíba: contornos derivados da malha municipal do IBGE, via repositório tbrugz/geodata-br (licença CC0 1.0, conferida em 18/11/2026) | 223 polígonos; a geometria de Cabedelo é corrigida na carga (`ST_MakeValid`) | 14/10/2026 |

Observações:
- O SINAN de 2023 e 2024 ainda pode ser revisado; uma nova extração pode mudar esses anos.
- O nome oficial vem do IBGE. A malha tem 3 nomes antigos (Santarém, Seridó, Campo de Santana); o IBGE usa Joca Claudino, São Vicente do Seridó e Tacima. O IBGE grafa "Quixaba", sem acento.
- Região de saúde: nomes oficiais do DATASUS sem o " - PB" (ex.: "1ª Região Mata Atlântica", "2ª Região"). A Base Territorial reflete a regionalização pactuada na CIB-PB; não foi conferida contra a resolução estadual vigente [VERIFICAR, opcional].
- Totais conferidos: 10.344 notificações, 223 municípios, 2.055.832 mulheres. A população de cada município conferiu, um a um, com a usada no painel enxuto.
