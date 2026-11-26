# Painel de Indicadores de Violência contra a Mulher na Paraíba

Painel web com as notificações de violência contra a mulher nos 223 municípios da Paraíba, de 2019 a 2024, a partir de dados públicos do SINAN e do Censo 2022.

**Acesse:** <https://anacamim.github.io/TCC/>

![Tela do mapa com a ficha de um município](capturas/1366_claro_mapa_ficha.png)

## Funcionalidades

- 5 indicadores por município, tipo de violência e período: casos notificados, taxa por 100 mil mulheres por ano, tipos de violência, faixa etária e comparação com a média da Paraíba.
- Filtros por indicador, tipo de violência, período (cada ano ou 2019 a 2024) e região de saúde.
- Mapa coroplético (taxa e comparação com a média) e de círculos proporcionais (casos).
- Ranking dos 10 maiores e dos 10 menores valores.
- Ficha do município, com impressão e link direto (`#mapa-<código IBGE>`).
- Comparação de 2 ou 3 municípios.
- Tabela dos municípios com download em CSV e exportação do mapa em PNG.
- Tela "Como calcular", com a fórmula e um exemplo de cada indicador.
- Temas claro e escuro; uso completo pelo teclado.

## Tecnologias

- **Banco de dados:** PostgreSQL 16 com PostGIS 3.4, em Docker
- **Pipeline:** Python 3 (biblioteca padrão; `extrair_munic2023.py` usa openpyxl)
- **Front-end:** HTML, CSS e JavaScript, sem framework, com Leaflet 1.9.4
- **Testes:** Playwright (Chrome, Firefox e WebKit)
- **Publicação:** GitHub Pages

## Arquitetura

```
dados/brutos/          arquivos originais (SINAN/TABNET, IBGE, DATASUS)
      │  pipeline/conferir.py
      ▼
PostgreSQL + PostGIS   sql/01_schema.sql, 02_carga.sql, 03_views_indicadores.sql
      │  pipeline/exportar.py
      ▼
web/dados.json         dados do painel (web/dados.js para abrir sem servidor)
      ▼
web/                   front-end estático
```

1. `conferir.py` confere os totais dos arquivos brutos.
2. A carga roda numa única transação e é desfeita se os totais não baterem (10.344 casos, 223 municípios, 2.055.832 mulheres).
3. As views SQL calculam os indicadores.
4. `exportar.py` gera `dados.json` e `dados.js` a partir do banco.
5. O front-end lê `dados.json` quando servido por http e `dados.js` quando aberto com duplo clique. Ele recalcula os indicadores para cada filtro com as mesmas fórmulas das views (`web/js/calculo.js`).

## Indicadores

| Indicador | Cálculo |
|---|---|
| Casos notificados | Notificações de mulheres, por município de residência, sem violência autoprovocada |
| Taxa por 100 mil mulheres por ano | casos ÷ mulheres × 100.000 ÷ número de anos |
| Tipos de violência | Casos de violência física, psicológica/moral e sexual |
| Faixa etária | Casos por faixa; taxa da faixa = casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6 |
| Comparação com a média da Paraíba | casos ÷ esperado, com esperado = mulheres do município × (casos da Paraíba ÷ mulheres da Paraíba) |

As fontes e datas de acesso de cada arquivo estão em [`dados/brutos/FONTES.md`](dados/brutos/FONTES.md).

## Como Executar

**Só o painel:** abra `web/index.html` no navegador, ou publique a pasta `web/` em um servidor estático.

**Do zero, a partir dos dados brutos.** Pré-requisitos: Windows, Docker Desktop aberto, Python 3 e Google Chrome.

```
atualizar.bat
```

O script confere os dados brutos, carrega o banco (container `pgtcc`, banco `websig`), cria as views, exporta os dados do painel e roda os testes. Na primeira execução, cria o ambiente `.venv` com o Playwright.

## Testes

| Arquivo | O que testa |
|---|---|
| `testes/testar_dados.py` | Totais e coerência do banco |
| `testes/testar_front.py` | Painel no navegador, comparado com as views, nos modos arquivo e servidor |
| `testes/testar_usabilidade.py` | Tarefas, contraste, daltonismo e tela de celular |

Os testes rodam no `atualizar.bat`. Para repeti-los no Firefox e no WebKit, use `testar_navegadores.bat`.

## Estrutura do Projeto

```
dados/brutos/   dados originais e FONTES.md
sql/            esquema, carga e views
pipeline/       scripts Python de conferência e exportação
web/            front-end (index.html, css/, js/, vendor/, fonts/)
testes/         testes automatizados
docs/           avaliação de usabilidade, bases avaliadas e relatórios do Lighthouse
```

## Autoria

Trabalho de Conclusão de Curso do Bacharelado em Sistemas de Informação, Universidade Federal da Paraíba (UFPB), Centro de Ciências Aplicadas e Educação (CCAE), 2026.

- **Autora:** Ana Clara Mendes Amim
- **Orientador:** Prof. Dr. José Adson Oliveira Guedes da Cunha

## Licença

Código sob a licença MIT ([`LICENSE`](LICENSE)). Textos, documentação e capturas de tela sob CC BY 4.0 ([`LICENSE-DOCS`](LICENSE-DOCS)).
