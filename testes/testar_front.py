"""Teste do front com Playwright (Chrome instalado). Compara o painel com a view SQL e confere as funções da tela.
- Dois modos de abertura: arquivo (duplo clique, usa dados.js) e servidor http (usa dados.json).
- Cálculo: taxa e observado ÷ esperado de todos os municípios × tipos × períodos = view (tolerância 0,01).
- Endereços (#mapa, #analise, #como-calcular, #mapa-<cod>), Copiar link, título com filtros, ranking maiores/menores,
  ficha (5 indicadores, links "como calcular", impressão), comparação, tabela do mapa, CSV (223 linhas = view).
- Só teclado; 1366x768, 1920x1080 e 390x844, claro e escuro; console sem erros. Capturas em capturas/.
Uso: python testes/testar_front.py   (requer: pip install playwright)"""
import csv
import functools
import http.server
import io
import pathlib
import sys
import tempfile
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pipeline"))
from banco import RAIZ, TOTAL_MUNICIPIOS, consulta  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

WEB = RAIZ / "web"
# Navegador: Chrome instalado (padrão) ou os do Playwright: python testes/<teste>.py --navegador firefox | webkit | chromium
NAV = sys.argv[sys.argv.index("--navegador") + 1] if "--navegador" in sys.argv else "chrome"


def lancar(pw):
    return pw.chromium.launch(channel="chrome", headless=True) if NAV == "chrome" else getattr(pw, NAV).launch(headless=True)


def movel(on=True):
    """Opções de celular. O Firefox do Playwright não emula is_mobile: lá só a tela pequena e o toque."""
    return {"has_touch": on, **({} if NAV == "firefox" else {"is_mobile": on})}
# As capturas oficiais saem do Chrome; nos outros navegadores vão para uma pasta temporária
CAP = RAIZ / "capturas" if NAV == "chrome" else pathlib.Path(tempfile.mkdtemp(prefix=f"websig_{NAV}_"))
CAP.mkdir(exist_ok=True)
TOL = 0.01
TELAS = {"mapa": "Mapa", "analise": "Análise", "como-calcular": "Como calcular"}
falhas, ok = [], []


def check(cond, msg):
    (ok if cond else falhas).append(msg)


def num_br(t):
    """'1.234,5 *' -> 1234.5"""
    return float(t.strip().split()[0].replace(".", "").replace(",", "."))


def fmt(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- referência: views SQL ----------
REF = {}
for r in consulta("SELECT cod_ibge7, nome, periodo, tipo, casos, taxa_100mil_ano, esperado, o_sobre_e FROM websig.vw_indicador_municipio_ano_tipo"):
    per = "all" if r["periodo"] == "2019-2024" else r["periodo"]
    REF[(r["cod_ibge7"], per, r["tipo"])] = {"nome": r["nome"], "casos": int(r["casos"]), "taxa": float(r["taxa_100mil_ano"]),
                                              "esp": float(r["esperado"]), "oe": float(r["o_sobre_e"])}
EST = {("all" if r["periodo"] == "2019-2024" else r["periodo"], r["tipo"]): float(r["taxa_100mil_ano"])
       for r in consulta("SELECT periodo, tipo, taxa_100mil_ano FROM websig.vw_indicador_estado")}
COD = {v["nome"]: k[0] for k, v in REF.items()}
SOUSA, SUME, JP = COD["Sousa"], COD["Sumé"], COD["João Pessoa"]
PEQUENO = min((v["casos"], k[0]) for k, v in REF.items() if k[1] == "all" and k[2] == "total")[1]
REGREF = {(r["cod_regiao"], "all" if r["periodo"] == "2019-2024" else r["periodo"], r["tipo"]): {"nome": r["regiao"], "taxa": float(r["taxa_100mil_ano"])}
          for r in consulta("SELECT cod_regiao, regiao, periodo, tipo, taxa_100mil_ano FROM websig.vw_indicador_regiao")}
MUNREG = {r["cod_ibge7"]: r["cod_regiao"] for r in consulta("SELECT m.cod_ibge7, r.cod_regiao FROM websig.regiao_saude r JOIN websig.municipio m USING (cod_ibge6)")}
POS_DICA = """(() => { const e = ALVO, t = document.getElementById('tip'), a = e.getBoundingClientRect(), b = t.getBoundingClientRect();
    return {tag: e.tagName.toLowerCase(), rot: e.getAttribute('aria-label') || '', tip: t.innerText, vis: getComputedStyle(t).display,
            cobre: !(b.bottom <= a.top || b.top >= a.bottom || b.right <= a.left || b.left >= a.right)}; })()"""   # etiqueta do mapa: visível, com o nome, sem cobrir o município (ALVO = o polígono)


class Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(WEB)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
MODOS = {"arquivo": (WEB / "index.html").as_uri(), "http": f"http://127.0.0.1:{srv.server_address[1]}/index.html"}

CALCULO = """() => { const P = window.PAINEL, tipos = ['total','fisica','psicologica','sexual'], pers = ['all', ...P.ANOS.map(String)], out = [];
  for (const f of P.F) { const p = f.properties;
    for (const t of tipos) for (const per of pers) out.push([p.cod, per, t, P.taxa(p, t, per), P.oe(p, t, per)]); }
  return out; }"""


def abrir(pg, url):
    pg.goto(url)
    pg.wait_for_function("window.PAINEL !== undefined", timeout=15000)
    pg.wait_for_selector("path.leaflet-interactive")


def ouvir(pg, lista):
    pg.on("pageerror", lambda e: lista.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and lista.append(m.text))


with sync_playwright() as pw:
    nav = lancar(pw)

    # ======================= funções da tela, nos dois modos de abertura =======================
    for modo, url in MODOS.items():
        ctx = nav.new_context(viewport={"width": 1366, "height": 768}, accept_downloads=True,
                              permissions=["clipboard-read", "clipboard-write"] if modo == "http" and NAV in ("chrome", "chromium") else [])
        pg = ctx.new_page(); erros = []; ouvir(pg, erros)
        abrir(pg, url)
        origem = pg.evaluate("window.PAINEL.origem")
        check(origem == ("dados.js" if modo == "arquivo" else "dados.json"), f"{modo}: dados carregados de {origem}")
        check(pg.locator("path.leaflet-interactive").count() == TOTAL_MUNICIPIOS, f"{modo}: {TOTAL_MUNICIPIOS} municípios no mapa")
        # 3 telas pelas abas
        for v, nome in TELAS.items():
            pg.click(f"button[role=tab][data-v={v}]"); pg.wait_for_timeout(300)
            check(pg.locator(f"#v-{v}").is_visible() and len(pg.inner_text(f"#v-{v}")) > 200 and pg.evaluate("location.hash") == f"#{v}",
                  f"{modo}: aba {nome} abre a tela e muda o endereço para #{v}")
        # Endereços digitados (link recebido de alguém)
        for v in TELAS:
            pg.goto(url + "#" + v); pg.wait_for_function("window.PAINEL !== undefined"); pg.wait_for_timeout(300)
            check(pg.locator(f"#v-{v}").is_visible(), f"{modo}: link #{v} abre a tela certa")
        pg.goto(url + "#mapa-" + SOUSA); pg.wait_for_function("window.PAINEL !== undefined"); pg.wait_for_timeout(700)
        check(pg.locator("#painel").is_visible() and "Sousa" in pg.inner_text("#painel h2"), f"{modo}: link #mapa-{SOUSA} abre a ficha de Sousa")
        pg.evaluate("location.hash = '#mapa'"); pg.wait_for_timeout(300)
        check(pg.locator("#painel").is_hidden(), f"{modo}: #mapa fecha a ficha")
        pg.go_back(); pg.wait_for_timeout(700)
        check(pg.locator("#painel").is_visible(), f"{modo}: botão Voltar do navegador reabre a ficha")
        if modo == "http" and NAV in ("chrome", "chromium"):   # leitura da área de transferência só é liberável no Chromium
            pg.click("#copiarLink"); pg.wait_for_timeout(200)
            check(pg.evaluate("navigator.clipboard.readText()").endswith("#mapa-" + SOUSA), "http: Copiar link copia o endereço da ficha")
        # Título com filtros ativos
        pg.evaluate("location.hash = '#mapa'"); pg.wait_for_timeout(200)
        pg.select_option("#tipo", "sexual"); pg.select_option("#per", "2024"); pg.wait_for_timeout(300)
        titulo = pg.inner_text("#mapatitulo")
        check(titulo == "Taxa por 100 mil mulheres · Sexual · 2024", f"{modo}: título do mapa '{titulo}'")
        # Tabela do mapa (mesmos filtros: sexual, 2024)
        pg.click("#verTabela"); pg.wait_for_timeout(300)
        linhas = pg.evaluate("() => [...document.querySelectorAll('#maptab tbody tr[data-c]')].map(tr => [tr.dataset.c, ...[...tr.querySelectorAll('td')].map(td => td.textContent)])")
        ruins = [ln[0] for ln in linhas if int(num_br(ln[3])) != REF[(ln[0], "2024", "sexual")]["casos"]
                 or abs(num_br(ln[4]) - REF[(ln[0], "2024", "sexual")]["taxa"]) > 0.05 + 1e-9 or abs(num_br(ln[5]) - REF[(ln[0], "2024", "sexual")]["oe"]) > 0.005 + 1e-9]
        check(len(linhas) == TOTAL_MUNICIPIOS and not ruins, f"{modo}: tabela do mapa com 223 linhas iguais à view (sexual, 2024; {len(ruins)} divergentes)")
        if modo == "http":
            pg.screenshot(path=str(CAP / "mapa_como_tabela.png"))
        pg.click("#verTabela"); pg.select_option("#tipo", "total"); pg.select_option("#per", "all"); pg.wait_for_timeout(300)
        # Ranking 10 maiores / 10 menores
        maiores = pg.evaluate("[...document.querySelectorAll('#rk a')].map(a => a.getAttribute('href').slice(6))")
        pg.click("#rk-menores"); pg.wait_for_timeout(200)
        menores = pg.evaluate("[...document.querySelectorAll('#rk a')].map(a => a.getAttribute('href').slice(6))")
        tx = [REF[(c, "all", "total")]["taxa"] for c in menores]
        check(len(maiores) == 10 and len(menores) == 10 and all(REF[(c, "all", "total")]["casos"] >= 10 for c in menores) and tx == sorted(tx)
              and "pelo menos 10 casos" in pg.inner_text("#rknota"), f"{modo}: ranking 10 maiores e 10 menores (menores só com 10+ casos, em ordem)")
        if modo == "http":
            pg.screenshot(path=str(CAP / "ranking_10_menores.png"))
        pg.click("#rk-maiores")
        # Região de saúde: recorta mapa, ranking e tabela; média da região na legenda = view
        RG = "25016"; dentro = {c for c, r in MUNREG.items() if r == RG}; rg = REGREF[(RG, "all", "total")]
        largura = "(() => { const b = PAINEL.limitesMapa(); return b.getEast() - b.getWest(); })()"
        z0 = pg.evaluate(largura)
        pg.select_option("#reg", RG); pg.wait_for_timeout(500)
        rk = pg.evaluate("[...document.querySelectorAll('#rk a')].map(a => a.getAttribute('href').slice(6))")
        z1 = pg.evaluate(largura)
        if modo == "http":
            pg.screenshot(path=str(CAP / "regiao_saude_filtro.png"))
        pg.click("#verTabela"); pg.wait_for_timeout(300)
        lin_reg = pg.evaluate("[...document.querySelectorAll('#maptab tbody tr[data-c]')].map(tr => tr.dataset.c)")
        pg.click("#verTabela"); pg.wait_for_timeout(200)
        check(rk and set(rk) <= dentro and set(lin_reg) == dentro and len(lin_reg) == len(dentro) and z1 < z0 and rg["nome"] in pg.inner_text("#mapatitulo")
              and f"Média da {rg['nome']}: {fmt(rg['taxa'], 1)}" in pg.inner_text("#leg"),
              f"{modo}: filtro de região de saúde recorta mapa, ranking e tabela ({len(lin_reg)} de {len(dentro)} municípios) e mostra a média da região")
        pg.select_option("#reg", ""); pg.wait_for_timeout(300)
        # Ficha: 5 indicadores comparados com o estado, links "como calcular", aviso de poucos casos
        pg.evaluate(f"location.hash = '#mapa-{SOUSA}'"); pg.wait_for_timeout(700)
        ficha = pg.inner_text("#painel"); r = REF[(SOUSA, "all", "total")]
        links = pg.evaluate("[...document.querySelectorAll('#painel a[data-ind]')].map(a => a.dataset.ind)")
        check(pg.locator("#painel .ind5 .it").count() == 5 and sorted(links) == ["casos", "faixa", "oe", "taxa", "tipos"]
              and fmt(r["taxa"], 1) in ficha and fmt(r["oe"], 2) in ficha and fmt(EST[("all", "total")], 1) in ficha and "Casos por ano" in ficha,
              f"{modo}: ficha de Sousa com 5 indicadores, média do estado, série anual e links 'como calcular'")
        rs = REGREF[(MUNREG[SOUSA], "all", "total")]
        check(f"Média da região de saúde ({rs['nome']}): {fmt(rs['taxa'], 1)}" in ficha, f"{modo}: ficha de Sousa com a média da região de saúde ({rs['nome']}) igual à view")
        pg.click("#painel a[data-ind=taxa]"); pg.wait_for_timeout(400)
        check(pg.evaluate("location.hash") == "#como-calcular" and "alvo" in (pg.get_attribute("#ind-taxa", "class") or ""), f"{modo}: link 'como calcular' leva à explicação da taxa")
        pg.evaluate(f"location.hash = '#mapa-{PEQUENO}'"); pg.wait_for_timeout(700)
        check("Poucos casos" in pg.inner_text("#painel"), f"{modo}: aviso de poucos casos no menor município")
        # Imprimir ficha: folha limpa só com a ficha
        pg.evaluate(f"location.hash = '#mapa-{SOUSA}'"); pg.wait_for_timeout(700)
        pg.evaluate("window.__imp = 0; window.print = function () { window.__imp++; }; 0")
        pg.click("#painel [data-acao=imprimir]")
        pg.emulate_media(media="print")
        vis = pg.evaluate("""() => ({imp: window.__imp, header: getComputedStyle(document.querySelector('header')).display, main: getComputedStyle(document.querySelector('main')).display,
            folha: getComputedStyle(document.getElementById('impressao')).display, texto: document.getElementById('impressao').innerText,
            botoes: [...document.querySelectorAll('#impressao button, #impressao a[data-ind]')].filter(b => b.getClientRects().length > 0).length})""")
        check(vis["imp"] == 1 and vis["header"] == "none" and vis["main"] == "none" and vis["folha"] == "block" and "Sousa" in vis["texto"]
              and "Fonte: SINAN" in vis["texto"] and vis["botoes"] == 0, f"{modo}: ficha impressa em folha limpa ({vis['header']}, {vis['folha']}, {vis['botoes']} botões)")
        if modo == "http":
            pg.screenshot(path=str(CAP / "ficha_impressa.png"), full_page=True)
            if NAV in ("chrome", "chromium"):   # PDF só existe no Chromium
                pg.pdf(path=str(CAP / "ficha_impressa_sousa.pdf"), format="A4")
        pg.emulate_media(media="screen"); pg.evaluate("window.dispatchEvent(new Event('afterprint'))")
        # Comparar 3 municípios
        pg.click("#painel [data-acao=comparar]"); pg.wait_for_timeout(200)
        pg.fill("#cmp2", "Sume"); pg.fill("#cmp3", "joao pessoa"); pg.wait_for_timeout(300)
        tab = pg.evaluate("""() => { const t = document.querySelector('#cmpRes table'); if (!t) return null;
            const cods = [...t.querySelectorAll('thead th[data-c]')].map(th => th.dataset.c);
            const linhas = {}; t.querySelectorAll('tbody tr:not(.grupo)').forEach(tr => { const td = [...tr.querySelectorAll('td')].map(x => x.textContent); linhas[td[0]] = td.slice(1); });
            return {cods, linhas, tipo: t.dataset.tipo, per: t.dataset.per}; }""")
        ok_cmp = bool(tab) and tab["cods"] == [SOUSA, SUME, JP]
        if ok_cmp:
            for i, c in enumerate(tab["cods"]):
                rr = REF[(c, tab["per"], tab["tipo"])]
                ok_cmp &= int(num_br(tab["linhas"]["Casos notificados"][i])) == rr["casos"]
                ok_cmp &= abs(num_br(tab["linhas"]["Taxa por 100 mil mulheres por ano"][i]) - rr["taxa"]) <= 0.05 + 1e-9
                ok_cmp &= abs(num_br(tab["linhas"]["Observado ÷ esperado"][i]) - rr["oe"]) <= 0.005 + 1e-9
            ok_cmp &= abs(num_br(tab["linhas"]["Taxa por 100 mil mulheres por ano"][-1]) - EST[(tab["per"], tab["tipo"])]) <= 0.05 + 1e-9
        check(ok_cmp, f"{modo}: comparação de 3 municípios lado a lado com a média do estado, igual à view")
        if modo == "http":
            pg.screenshot(path=str(CAP / "comparar_municipios.png"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
        check(not pg.evaluate("document.getElementById('cmp').open"), f"{modo}: Esc fecha a comparação")
        # Cálculo do painel × view, todas as combinações
        calc = pg.evaluate(CALCULO)
        dif = [x for x in calc if abs(x[3] - REF[(x[0], x[1], x[2])]["taxa"]) > TOL or abs(x[4] - REF[(x[0], x[1], x[2])]["oe"]) > TOL]
        check(len(calc) == len(REF) and not dif, f"{modo}: painel × SQL em {len(calc)} combinações ({len(dif)} acima de {TOL})")
        calc_reg = pg.evaluate("""(() => { const P = PAINEL, out = []; for (const r of Object.keys(P.REG)) for (const t of ['total','fisica','psicologica','sexual'])
            for (const per of ['all', ...P.ANOS.map(String)]) out.push([r, per, t, P.taxaRegiao(r, t, per)]); return out; })()""")
        dif = [x for x in calc_reg if abs(x[3] - REGREF[(x[0], x[1], x[2])]["taxa"]) > TOL]
        check(len(calc_reg) == len(REGREF) == 16 * 7 * 4 and not dif, f"{modo}: taxa das 16 regiões de saúde × SQL em {len(calc_reg)} combinações ({len(dif)} divergentes)")
        # Tabela da Análise (arredondamento) e CSV
        pg.evaluate("location.hash = '#analise'"); pg.wait_for_timeout(300)
        for t in ["total", "fisica", "psicologica", "sexual"]:
            pg.select_option("#ttipo", t)
            lin = pg.evaluate("() => [...document.querySelectorAll('#tab tbody tr[data-c]')].map(tr => [tr.dataset.c, ...[...tr.querySelectorAll('td')].map(td => td.textContent)])")
            ruins = [ln[0] for ln in lin if abs(num_br(ln[4]) - REF[(ln[0], "all", t)]["taxa"]) > 0.05 + 1e-9 or abs(num_br(ln[5]) - REF[(ln[0], "all", t)]["oe"]) > 0.005 + 1e-9]
            check(len(lin) == TOTAL_MUNICIPIOS and not ruins, f"{modo}: tabela da Análise ({t}) igual à view ({len(ruins)} divergentes)")
            with pg.expect_download() as dl:
                pg.click("#baixarCsv")
            arq = dl.value.path()
            texto = pathlib.Path(arq).read_text(encoding="utf-8")
            rows = list(csv.DictReader(io.StringIO(texto.lstrip("﻿")), delimiter=";"))
            dec = lambda s: float(s.replace(",", "."))
            ruins = [x["cod_ibge7"] for x in rows if int(x["casos_2019_2024"]) != REF[(x["cod_ibge7"], "all", t)]["casos"]
                     or abs(dec(x["taxa_100mil_mulheres_ano"]) - REF[(x["cod_ibge7"], "all", t)]["taxa"]) > TOL
                     or abs(dec(x["casos_esperados"]) - REF[(x["cod_ibge7"], "all", t)]["esp"]) > TOL
                     or abs(dec(x["observado_sobre_esperado"]) - REF[(x["cod_ibge7"], "all", t)]["oe"]) > TOL]
            check(texto.startswith("﻿") and len(rows) == TOTAL_MUNICIPIOS and len({x["cod_ibge7"] for x in rows}) == TOTAL_MUNICIPIOS and not ruins,
                  f"{modo}: CSV ({t}) com 223 linhas iguais à view ({len(ruins)} divergentes)")
            if modo == "http" and t == "total":
                (CAP / "exemplo_tabela_total.csv").write_text(texto, encoding="utf-8")
        check(not erros, f"{modo}: console sem erros {erros[:2]}")
        ctx.close()

    # ======================= só teclado =======================
    ctx = nav.new_context(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page(); erros_k = []; ouvir(pg, erros_k)
    abrir(pg, MODOS["http"])
    vistos, ids = [], {"copiarLink", "ind", "tipo", "per", "reg", "busca", "verTabela", "abrirComparar", "rk-maiores", "rk-menores"}
    for _ in range(40):
        pg.keyboard.press("Tab")
        el = pg.evaluate("(() => { const e = document.activeElement; return {id: e.id, tab: e.dataset.v || '', href: e.getAttribute('href') || '', outline: getComputedStyle(e).outlineStyle}; })()")
        vistos.append(el)
    alcancados = {e["id"] for e in vistos} | {"tab-" + e["tab"] for e in vistos if e["tab"]}
    faltam = (ids | {"tab-mapa"}) - alcancados
    check(not faltam and all(e["outline"] != "none" for e in vistos if e["id"] or e["tab"]), f"teclado: todos os controles alcançáveis com Tab e com foco visível (faltam {sorted(faltam)})")
    check(vistos[0]["href"] == "#conteudo", "teclado: o primeiro Tab mostra 'Pular para o conteúdo'")
    pg.focus("#tab-mapa"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    seta = pg.evaluate("[document.activeElement.id, location.hash, document.title]")
    pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(300)
    check(seta[0] == "tab-analise" and seta[1] == "#analise" and seta[2].startswith("Análise") and pg.evaluate("location.hash") == "#mapa",
          f"teclado: setas trocam de aba e o título da página acompanha ({seta})")
    pg.focus("#rk a"); pg.keyboard.press("Enter"); pg.wait_for_timeout(700)
    check(pg.locator("#painel").is_visible() and pg.evaluate("location.hash").startswith("#mapa-"), "teclado: Enter num item do ranking abre a ficha")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    foco = pg.evaluate("(() => { const e = document.activeElement; return e.id || (e.closest('#rk') ? 'rk' : e.tagName); })()")
    check(not pg.locator("#painel").is_visible() and foco in ("rk", "mapatitulo"), f"teclado: Esc fecha a ficha e o foco volta ao ranking ({foco})")
    # municípios do mapa pelo teclado: Tab percorre, etiqueta aparece sem cobrir, Enter abre a ficha
    pg.focus("#map"); pg.keyboard.press("Tab"); pg.wait_for_timeout(250)
    k = pg.evaluate(POS_DICA.replace("ALVO", "document.activeElement"))
    nome_k = k["rot"].split(":")[0]
    check(k["tag"] == "path" and k["vis"] == "block" and nome_k and nome_k in k["tip"] and not k["cobre"],
          f"teclado: Tab chega aos municípios do mapa, com etiqueta nome + valor que não cobre o município ({k['tip']!r})")
    pg.screenshot(path=str(CAP / "mapa_foco_teclado.png"))
    pg.keyboard.press("Enter"); pg.wait_for_timeout(700)
    check(pg.locator("#painel").is_visible() and nome_k in pg.inner_text("#painel h2"), f"teclado: Enter num município do mapa abre a ficha ({nome_k})")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    pg.focus("#abrirComparar"); pg.keyboard.press("Enter"); pg.wait_for_timeout(200)
    pg.keyboard.type("Sousa"); pg.keyboard.press("Tab"); pg.keyboard.type("Patos"); pg.wait_for_timeout(300)
    check(pg.evaluate("document.getElementById('cmp').open") and pg.locator("#cmpRes table").count() == 1, "teclado: comparar municípios só com o teclado")
    # No Firefox o 1º Esc fecha a lista de sugestões do campo (comportamento do navegador); o 2º fecha a janela
    esc = 0
    while pg.evaluate("document.getElementById('cmp').open") and esc < 2:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200); esc += 1
    check(not pg.evaluate("document.getElementById('cmp').open"), f"teclado: Esc fecha a comparação ({esc} toque(s) em Esc)")
    pg.focus("button[data-v=analise]"); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
    pg.focus("#tab th[data-k=taxa]"); pg.keyboard.press("Enter"); pg.wait_for_timeout(200)
    check(pg.locator("#v-analise").is_visible() and pg.get_attribute("#tab th[data-k=taxa]", "aria-sort") == "descending", "teclado: abrir Análise e ordenar a tabela com Enter")
    check(not erros_k, f"teclado: console sem erros {erros_k[:2]}")
    ctx.close()

    # ======================= toque (celular): 1º toque mostra a etiqueta, 2º abre a ficha =======================
    ctx = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, **movel())
    pg = ctx.new_page(); erros_t = []; ouvir(pg, erros_t)
    abrir(pg, MODOS["http"])
    pg.locator("#map").scroll_into_view_if_needed(); pg.wait_for_timeout(700)   # espera o enquadramento inicial do mapa terminar
    PATOS = COD["Patos"]; SEL = f"document.querySelector('path[aria-label^=\"Patos:\"]')"
    alvo = pg.evaluate(f"""(() => {{ const e = {SEL}, r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2; let best = null;
        for (let i = 0; i <= 20; i++) for (let j = 0; j <= 20; j++) {{ const x = r.left + r.width * i / 20, y = r.top + r.height * j / 20;
          if (document.elementFromPoint(x, y) === e) {{ const d = (x - cx) ** 2 + (y - cy) ** 2; if (!best || d < best[2]) best = [x, y, d]; }} }}
        return best; }})()""")
    pg.touchscreen.tap(alvo[0], alvo[1]); pg.wait_for_timeout(400)
    t1 = pg.evaluate(POS_DICA.replace("ALVO", SEL)); h1 = pg.evaluate("location.hash")
    pg.screenshot(path=str(CAP / "celular_toque_etiqueta.png"))
    pg.touchscreen.tap(alvo[0], alvo[1]); pg.wait_for_timeout(800)
    check(t1["vis"] == "block" and "Patos" in t1["tip"] and not t1["cobre"] and h1 in ("", "#mapa") and pg.evaluate("location.hash") == "#mapa-" + PATOS and not erros_t,
          f"toque: 1º toque mostra a etiqueta acima do município ({t1['tip']!r}), 2º abre a ficha {erros_t[:1]}")
    ctx.close()

    # ======================= tamanhos e temas =======================
    for (w, h, nome) in [(1366, 768, "1366"), (1920, 1080, "1920"), (390, 844, "celular")]:
        for tema in ["light", "dark"]:
            cel = nome == "celular"
            ctx = nav.new_context(viewport={"width": w, "height": h}, color_scheme=tema, device_scale_factor=2 if cel else 1, **movel(cel))
            pg = ctx.new_page(); erros_t = []; ouvir(pg, erros_t)
            abrir(pg, MODOS["http"] + "#mapa-" + SOUSA); pg.wait_for_timeout(800)
            rot = f"{nome}_{'claro' if tema == 'light' else 'escuro'}"
            sem_rol = pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            pg.screenshot(path=str(CAP / f"{rot}_mapa_ficha.png"))
            pg.evaluate("location.hash = '#analise'"); pg.wait_for_timeout(400)
            pg.screenshot(path=str(CAP / f"{rot}_analise.png"))
            pg.evaluate("location.hash = '#como-calcular'"); pg.wait_for_timeout(300)
            if nome == "1366":
                pg.screenshot(path=str(CAP / f"{rot}_como_calcular.png"))
            check(sem_rol and pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1") and not erros_t, f"{rot}: sem rolagem lateral e console sem erros {erros_t[:1]}")
            ctx.close()
    nav.close()
srv.shutdown()

print(f"Teste do front ({NAV}): {len(ok)} verificações OK, {len(falhas)} falhas")
for f in falhas:
    print("  FALHA:", f)
sys.exit(1 if falhas else 0)
