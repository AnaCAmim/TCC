# Lighthouse do painel

Lighthouse 12.6.0, Chrome sem janela, página inicial (`index.html`) servida localmente, primeira visita (com a tela "Sobre o painel" aberta).

| Relatório | Data | Servidor | Desempenho | Acessibilidade | Boas práticas | SEO |
|---|---|---|---|---|---|---|
| `lighthouse_celular.report.html` | 22/11/2026, layout do mapa (legenda compacta, canvas claro, mapa maior) | com compressão gzip (como o GitHub Pages) | 98 | 100 | 100 | 100 |
| `lighthouse_computador.report.html` (perfil desktop) | 22/11/2026, layout do mapa | com compressão gzip | 100 | 100 | 100 | 100 |
| `lighthouse_celular_sem_compressao.report.html` | 18/11/2026 | `python -m http.server` (sem compressão) | 85 | 100 | 100 | 100 |

Metas: Acessibilidade ≥ 95 e Desempenho ≥ 90, atingidas no servidor com compressão.

Histórico do celular, com compressão:
- 18/11/2026, antes do visual de relatório: Desempenho 99, Acessibilidade 100.
- 20/11/2026, revisão visual (paletas ColorBrewer, legenda fixa, gráficos neutros): 93, 97, 98 e 97 em quatro rodadas (mediana 97,5; a de 93 teve a primeira pintura mais lenta). Relatório guardado: 98.
- 20/11/2026, melhorias cartográficas: 95 na primeira versão (o mapa era desenhado e reenquadrado na abertura; contornos maiores). Com a vista calculada antes de desenhar as camadas e os contornos e rótulos adiados para depois do primeiro desenho: 97 e 98 (relatório guardado: 98).
- 22/11/2026, layout do mapa (legenda compacta, canvas claro no tema escuro, enquadramento pelo contorno real): 98, 97 e 96 em três rodadas (mediana 97). Relatório guardado: 98. Computador 100.
- 20/11/2026, com as fontes IBM Plex: 96 sem pré-carregamento das fontes; 99 em duas rodadas com o pré-carregamento (feito só quando o painel é servido por http, porque o navegador o bloqueia no duplo clique).

Sem compressão, o celular simulado (rede 4G lenta) recebe os 250 KB do `dados.json` e os 150 KB do Leaflet inteiros, e o desempenho cai para 85. Por isso o painel deve ser publicado num servidor que comprima os arquivos, como o GitHub Pages.

Antes do acabamento de 18/11 (servidor sem compressão), o resultado era: Desempenho 75, Acessibilidade 100, Boas práticas 100, SEO 89. As mudanças estão em `docs/websig_usabilidade.md`.
