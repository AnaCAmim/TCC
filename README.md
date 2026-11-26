# Painel de Indicadores de Violência contra a Mulher na Paraíba

Trabalho de Conclusão de Curso · Bacharelado em Sistemas de Informação · UFPB, Centro de Ciências Aplicadas e Educação (CCAE) · 2026<br>
Autora: Ana Clara Mendes Amim<br>
Orientador: Prof. Dr. José Adson Oliveira Guedes da Cunha

Painel publicado: <https://anacamim.github.io/TCC/>

Painel web com as notificações de violência contra a mulher nos 223 municípios da Paraíba, de 2019 a 2024 (SINAN). Mostra 5 indicadores por município, tipo de violência e período: casos notificados, taxa por 100 mil mulheres por ano, tipos de violência, faixa etária e comparação com a média da Paraíba (observado ÷ esperado).

![Mapa com a ficha de um município](capturas/1366_claro_mapa_ficha.png)

## Arquitetura

```
dados/brutos/            arquivos originais (TABNET/SINAN, IBGE, DATASUS)
      │  pipeline/conferir.py          confere os totais dos arquivos
      ▼
PostgreSQL 16 + PostGIS 3.4 (Docker)
      │  sql/01_schema.sql             tabelas
      │  sql/02_carga.sql              carga numa transação; aborta se os totais não baterem
      │  sql/03_views_indicadores.sql  fórmulas dos indicadores (views)
      ▼
pipeline/exportar.py     gera web/dados.json e web/dados.js a partir das views
      ▼
web/                     front estático: HTML, CSS, JavaScript e Leaflet
```

- **Banco.** Os indicadores são calculados nas views SQL. A carga confere os totais validados (10.344 casos, 223 municípios, 2.055.832 mulheres) e, se algo não bater, desfaz tudo e mantém o banco anterior.
- **Exportação.** `exportar.py` junta as views, a malha municipal e os contornos do estado e das 16 regiões de saúde (`ST_Union` no PostGIS) num único `dados.json`. O `dados.js` tem o mesmo conteúdo, para abrir o painel sem servidor.
- **Front.** Página estática, sem framework e sem etapa de build. Lê `dados.json` quando servida por http (GitHub Pages) e `dados.js` quando aberta com duplo clique. O JavaScript fica em scripts comuns, sem módulos ES, porque o navegador bloqueia módulos em `file://`. Módulos em `web/js/`: `dados` (carga), `calculo` (as mesmas fórmulas das views), `mapa` (mapa, legenda, ranking e ficha), `analise` (gráficos e tabela), `tour`, `util` e `app` (telas e endereços).
- **Coerência.** O front recalcula os indicadores para cada filtro com as mesmas fórmulas das views, e um teste compara os dois resultados nas 6.244 combinações de município, tipo e período.

Telas: **Mapa** (filtros, mapa coroplético ou de círculos proporcionais, ranking e ficha do município), **Análise** (gráficos, tabela e CSV) e **Como calcular** (fórmula e exemplo de cada indicador).

## Tecnologias

PostgreSQL 16, PostGIS 3.4, Docker, Python 3 (biblioteca padrão no pipeline; Playwright nos testes), HTML, CSS, JavaScript, Leaflet 1.9.4 e GitHub Pages.

## Indicadores

| Indicador | Cálculo |
|---|---|
| Casos notificados | Contagem do SINAN: mulheres, município de residência, sem violência autoprovocada |
| Taxa por 100 mil mulheres por ano | casos ÷ mulheres × 100.000 ÷ número de anos |
| Tipos de violência | Casos de violência física, psicológica/moral e sexual (uma notificação pode ter mais de um tipo) |
| Faixa etária | Casos por faixa; taxa da faixa = casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6 |
| Comparação com a média da Paraíba | esperado = mulheres do município × (casos da Paraíba ÷ mulheres da Paraíba); índice = casos ÷ esperado |

Denominador: mulheres do Censo 2022 (IBGE). Views: `vw_indicador_municipio_ano_tipo`, `vw_indicador_estado`, `vw_indicador_regiao`, `vw_faixa_municipio`, `vw_faixa_estado`, `vw_local_atendimento` e `vw_local_estado`.

Fontes: SINAN/TABNET (Ministério da Saúde), IBGE (Censo 2022, SIDRA 9514, MUNIC 2023 e localidades), DATASUS (Base Territorial, regiões de saúde) e malha municipal via tbrugz/geodata-br (CC0). Detalhes em [`dados/brutos/FONTES.md`](dados/brutos/FONTES.md).

## Como Rodar

- **Só o painel:** duplo clique em `web/index.html`, ou publicar a pasta `web/` em qualquer servidor estático.
- **Tudo a partir dos dados brutos** (Windows, Docker Desktop e Python 3): `atualizar.bat` confere os brutos, carrega o banco (container `pgtcc`, banco `websig`), cria as views, exporta os dados do painel e roda os testes.

## Testes

- `testes/testar_dados.py`: totais e coerência do banco (67 verificações).
- `testes/testar_front.py`: o painel com Playwright, nos dois modos de abertura, comparado com as views (169 verificações).
- `testes/testar_usabilidade.py`: tarefas, contraste, daltonismo e celular (34 verificações).

`testar_navegadores.bat` repete os dois últimos no Firefox e no WebKit.

## Estrutura

```
dados/brutos/   arquivos originais e FONTES.md
sql/            esquema, carga e views
pipeline/       conferir.py, exportar.py, banco.py, extrair_munic2023.py
web/            o painel (index.html, css/, js/, vendor/leaflet, fonts/, dados.json, dados.js)
testes/         testes automatizados e gerador do material do teste com usuários
docs/           avaliação de usabilidade, bases avaliadas, Lighthouse, teste com usuários
```

Documentação: [`docs/websig_usabilidade.md`](docs/websig_usabilidade.md) (avaliação de usabilidade e acessibilidade), [`docs/bases_candidatas.md`](docs/bases_candidatas.md), [`docs/lighthouse/`](docs/lighthouse/) e [`docs/teste_usuarios/`](docs/teste_usuarios/).

## Licença

Código sob licença MIT ([`LICENSE`](LICENSE)); textos, documentação e capturas sob CC BY 4.0 ([`LICENSE-DOCS`](LICENSE-DOCS)). Leaflet (BSD 2-Clause) e IBM Plex (SIL OFL) têm licenças próprias.
