# Lighthouse do painel (18/11/2026)

Lighthouse 12.6.0, Chrome sem janela, página inicial (`index.html`) servida localmente, primeira visita (com a tela "Sobre o painel" aberta).

| Relatório | Servidor | Desempenho | Acessibilidade | Boas práticas | SEO |
|---|---|---|---|---|---|
| `lighthouse_celular.report.html` | com compressão gzip (como o GitHub Pages) | 99 | 100 | 100 | 100 |
| `lighthouse_computador.report.html` (perfil desktop) | com compressão gzip | 100 | 100 | 100 | 100 |
| `lighthouse_celular_sem_compressao.report.html` | `python -m http.server` (sem compressão) | 85 | 100 | 100 | 100 |

Metas: Acessibilidade ≥ 95 e Desempenho ≥ 90. Ambas foram atingidas no servidor com compressão. Sem compressão, o celular simulado (rede 4G lenta) recebe os 250 KB do `dados.json` e os 150 KB do Leaflet inteiros, e o desempenho cai para 85. Por isso o painel deve ser publicado num servidor que comprima os arquivos, o que o GitHub Pages faz.

Antes dos ajustes desta etapa (servidor sem compressão), o resultado era: Desempenho 75, Acessibilidade 100, Boas práticas 100, SEO 89. O que mudou está em `docs/websig_usabilidade.md`, na seção "Acabamento para a apresentação".
