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
import re
import random
import shutil
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


def npct(v):
    """Porcentagem como no painel: sem casas acima de 10%; uma casa até 10%."""
    return (fmt(v, 0) if v >= 10 else fmt(v, 1)) + "%"


GEOM = """(() => { const m = document.getElementById('map').getBoundingClientRect(), e = PAINEL.enquadramento(), leg = document.getElementById('leg'), pn = document.getElementById('painel');
    const R = el => { if (!el) return null; const r = el.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom] : null; };
    return { est: [m.left + e.x0, m.top + e.y0, m.left + e.x1, m.top + e.y1], leg: R(leg), ficha: getComputedStyle(pn).display !== 'none' ? R(pn) : null,
      ctl: R(document.querySelector('#map .leaflet-top.leaflet-left')), tit: R(document.getElementById('mapatitulo')), mapa: [m.left, m.top, m.right, m.bottom],
      rol: Math.max(leg.scrollHeight - leg.clientHeight, leg.scrollWidth - leg.clientWidth), linhas: [...leg.querySelectorAll('.row')].map(r => Math.round(r.getBoundingClientRect().height)),
      ler: !!leg.querySelector('details.leg-ler:not([open]) small'), toca: (() => {
        // o contorno desenhado do estado toca cada retângulo? (600 pontos da linha + cantos e centro do retângulo dentro do estado)
        const ep = document.querySelector('.leaflet-estado-pane path'), o = {};
        if (!ep) return null;
        const M = ep.getScreenCTM(), inv = M.inverse(), n = ep.getTotalLength(), pts = [];
        for (let i = 0; i < 600; i++) { const q = ep.getPointAtLength(n * i / 600); pts.push(new DOMPoint(q.x, q.y).matrixTransform(M)); }
        const fill = (x, y) => ep.isPointInFill(new DOMPoint(x, y).matrixTransform(inv));
        Object.entries({ leg, ficha: getComputedStyle(pn).display !== 'none' ? pn : null, ctl: document.querySelector('#map .leaflet-top.leaflet-left'), tit: document.getElementById('mapatitulo') }).forEach(([k, el]) => {
          if (!el) { o[k] = false; return; }
          const r = el.getBoundingClientRect();
          o[k] = pts.some(q => q.x > r.left && q.x < r.right && q.y > r.top && q.y < r.bottom) || [[r.left + 1, r.top + 1], [r.right - 1, r.top + 1], [r.left + 1, r.bottom - 1], [r.right - 1, r.bottom - 1], [(r.left + r.right) / 2, (r.top + r.bottom) / 2]].some(([x, y]) => fill(x, y));
        });
        return o; })() }; })()"""


def bate(a, b):
    """Retângulos [esq, topo, dir, base] se sobrepõem?"""
    return bool(a and b) and not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


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
FXREF = {(r["cod_ibge7"], int(r["faixa_id"])): (int(r["casos"]), float(r["taxa_100mil_ano"])) for r in consulta(
    "SELECT cod_ibge7, faixa_id, casos, taxa_100mil_ano FROM websig.vw_faixa_municipio WHERE faixa_id <= 10")}
FXEST = {int(r["faixa_id"]): float(r["taxa_100mil_ano"]) for r in consulta("SELECT faixa_id, taxa_100mil_ano FROM websig.vw_faixa_estado WHERE faixa_id <= 10")}
with open(RAIZ / "dados" / "brutos" / "ibge_munic2023_rede_atendimento_pb.csv", encoding="utf-8") as _f:
    REDE_BRUTO = {r["cod_ibge7"]: r for r in csv.DictReader(_f)}
COLS_REDE = ["organismo_politicas_mulheres", "centro_referencia", "casa_abrigo", "delegacia_mulher"]
LOCREF = {(r["cod_ibge7"], int(r["categoria"])): (int(r["casos"]), int(r["total"]), float(r["pct"]) if r["pct"] not in ("", None) else None)
          for r in consulta("SELECT cod_ibge7, categoria, casos, total, pct FROM websig.vw_local_atendimento")}
LOCEST = {int(r["categoria"]): (int(r["casos"]), float(r["pct"])) for r in consulta("SELECT categoria, casos, pct FROM websig.vw_local_estado")}
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



CHAVE_SOBRE = "websig-sobre-visto"


def visita_repetida(nav):
    """Os testes simulam quem já viu "Sobre o painel" (o aviso da 1ª visita é testado à parte). Devolve o new_context original."""
    original = nav.new_context

    def novo(**kw):
        ctx = original(**kw)
        ctx.add_init_script(f"try {{ localStorage.setItem('{CHAVE_SOBRE}', '1'); }} catch (e) {{}}")
        return ctx
    nav.new_context = novo
    return original


def abrir(pg, url):
    pg.goto(url)
    pg.wait_for_function("window.PAINEL !== undefined", timeout=15000)
    pg.wait_for_selector("path.leaflet-interactive")


def ouvir(pg, lista):
    pg.on("pageerror", lambda e: lista.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and lista.append(m.text))


with sync_playwright() as pw:
    nav = lancar(pw)
    ctx_puro = visita_repetida(nav)

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
        check(titulo == "Taxa por 100 mil mulheres por ano · Sexual · 2024", f"{modo}: título do mapa '{titulo}'")
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
        # ---- Cartografia ----
        # Valor instável: hachura nos municípios com menos de 10 casos (taxa e observado ÷ esperado), item na legenda
        hach = pg.evaluate("""(() => ({ fill: [...document.querySelectorAll('path.leaflet-interactive')].filter(p => (p.getAttribute('fill') || '').startsWith('url(#hach-')).length,
            padroes: document.querySelectorAll('pattern[id^=hach-]').length,
            leg: (document.querySelector('#leg .row.inst .cont') || {}).textContent,
            cont: [...document.querySelectorAll('#leg .row[data-n]')].reduce((s, r) => s + +r.dataset.n, 0) }))()""")
        n_inst = sum(1 for (c, per, t), v in REF.items() if per == "all" and t == "total" and v["casos"] < 10)
        check(hach["fill"] == n_inst and hach["padroes"] >= 4 and hach["leg"] == str(n_inst) and hach["cont"] == TOTAL_MUNICIPIOS,
              f"{modo}: hachura nos {hach['fill']} municípios com menos de 10 casos (view: {n_inst}), item na legenda e contagem por classe somando 223")
        # ---- Revisão visual: paletas ColorBrewer, classes fixas, hachura opcional, legenda ----
        YLORRD = {"#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"}; PUOR = {"#5e3c99", "#b2abd2", "#f7f7f7", "#fdb863", "#e66101"}
        CORES = """(() => { const f = [...document.querySelectorAll('path.leaflet-interactive[data-instavel]')].map(p => p.getAttribute('fill'));
            const pad = [...document.querySelectorAll('pattern[id^=hach-] rect')].map(r => r.getAttribute('fill'));
            return { cores: [...new Set(f.filter(x => !x.startsWith('url')).concat(pad))].map(x => x.toLowerCase()), hist: document.querySelectorAll('#leg .hist').length,
                     rot: [...document.querySelectorAll('#leg .row[data-n]')].map(e => e.dataset.rot), lim: [...document.querySelectorAll('#leg .row[data-n]')].map(e => e.dataset.lim || ''),
                     media: [...document.querySelectorAll('#leg .row[data-n] .media')].length }; })()"""
        v_taxa = pg.evaluate(CORES)
        pg.select_option("#per", "2024"); pg.wait_for_timeout(300)
        v_2024 = pg.evaluate(CORES)
        pg.select_option("#tipo", "sexual"); pg.wait_for_timeout(300)
        v_sex = pg.evaluate(CORES)
        pg.select_option("#tipo", "total"); pg.select_option("#per", "all"); pg.select_option("#ind", "oe"); pg.wait_for_timeout(300)
        v_oe = pg.evaluate(CORES)
        check(set(v_taxa["cores"]) <= YLORRD and v_taxa["rot"] == v_2024["rot"] == ["menos de 40", "40 a 60", "60 a 90", "90 a 140", "140 ou mais"] and v_sex["rot"] != v_taxa["rot"]
              and v_taxa["hist"] == 0 and v_taxa["media"] == 1 and set(v_oe["cores"]) <= PUOR and v_oe["hist"] == 5
              and v_oe["rot"] == ["muito abaixo da média (menos da metade)", "abaixo da média", "perto da média", "acima da média", "muito acima da média (mais do dobro)"]
              and v_oe["lim"] == ["menos de 0,5", "0,5 a 0,8", "0,8 a 1,25", "1,25 a 2", "2 ou mais"],
              f"{modo}: taxa em YlOrRd com classes fixas iguais em 2019–2024 e em 2024 ({v_taxa['rot']}); comparação com a média em PuOr, em palavras, com os limites em letra menor")
        pg.uncheck("#destacarPoucos"); pg.wait_for_timeout(200)
        sem_hach = pg.evaluate("[...document.querySelectorAll('path.leaflet-interactive')].filter(p => (p.getAttribute('fill') || '').startsWith('url(#hach-')).length")
        sem_item = pg.locator("#leg .row.inst").count()
        pg.check("#destacarPoucos"); pg.wait_for_timeout(200)
        check(sem_hach == 0 and sem_item == 0 and pg.evaluate("[...document.querySelectorAll('path.leaflet-interactive')].filter(p => (p.getAttribute('fill') || '').startsWith('url(#hach-')).length") == n_inst,
              f"{modo}: opção 'Destacar municípios com poucos casos' liga e desliga a hachura e o item da legenda")
        pg.select_option("#ind", "taxa"); pg.wait_for_timeout(300)
        # Casos: símbolos proporcionais (área ∝ casos, raio pela raiz quadrada; maiores atrás) sobre base cinza
        pg.select_option("#ind", "casos"); pg.wait_for_timeout(400)
        sim = pg.evaluate("PAINEL.simbolos()")
        casos_all = {c: v["casos"] for (c, per, t), v in REF.items() if per == "all" and t == "total"}
        vmax = max(casos_all.values()); CG = COD["Campina Grande"]
        ok_area = sim["escala"] and sim["escala"]["vmax"] == vmax and all(
            abs(sim["raios"][c] - sim["escala"]["rmax"] * (casos_all[c] / vmax) ** 0.5) < 1e-6 for c in (JP, CG, SOUSA))
        razoes = [sim["raios"][c] ** 2 / casos_all[c] for c in (JP, CG, SOUSA)]   # área ∝ casos: r² ÷ casos constante
        ordem = [casos_all[c] for c in sim["ordem"]]
        base = pg.evaluate("new Set([...document.querySelectorAll('path.leaflet-interactive[data-instavel]')].map(p => p.getAttribute('fill'))).size")
        check(ok_area and max(razoes) - min(razoes) < 1e-9 and ordem == sorted(ordem, reverse=True) and len(sim["ordem"]) == sum(1 for v in casos_all.values() if v > 0)
              and base == 1 and pg.locator("#leg svg.circ circle").count() == 3,
              f"{modo}: casos em símbolos proporcionais (área de João Pessoa, Campina Grande e Sousa ∝ casos; maiores atrás; base cinza; 3 círculos na legenda)")
        if modo == "http":
            pg.screenshot(path=str(CAP / "mapa_simbolos_casos.png"))
        sem_ponto = pg.evaluate("[...document.querySelectorAll('.rotulo')].every(e => getComputedStyle(e, '::before').display === 'none')")
        check(sem_ponto and pg.evaluate("getComputedStyle(document.querySelector('path.leaflet-interactive[data-instavel]')).fill !== ''"),
              f"{modo}: mapa de casos com rótulos das cidades sem os pontos (só texto com halo)")
        # Baixar mapa (PNG): imagem com título, legenda e fonte, nos dois modos de abertura
        with pg.expect_download(timeout=20000) as dl:
            pg.click("#baixarPng")
        png = pathlib.Path(dl.value.path()).read_bytes()
        larg_mapa = pg.evaluate("PAINEL.enquadramento().w")
        check(png[:8] == b"\x89PNG\r\n\x1a\n" and int.from_bytes(png[16:20], "big") == (larg_mapa + 300) * 2 and len(png) > 50000 and dl.value.suggested_filename.startswith("mapa_casos_total"),
              f"{modo}: Baixar mapa (PNG) gera a imagem do mapa atual ({len(png)} bytes, {dl.value.suggested_filename})")
        if modo == "http":
            (CAP / "mapa_exportado_casos.png").write_bytes(png)
        pg.select_option("#ind", "taxa"); pg.wait_for_timeout(300)
        # Rótulos das cidades-polo: visíveis e sem sobreposição
        rot = pg.evaluate("""(() => { const v = [...document.querySelectorAll('.rotulo')].filter(e => e.style.visibility !== 'hidden').map(e => [e.textContent, e.firstChild.getBoundingClientRect()]);
            const bate = v.some(([, a], i) => v.some(([, b], j) => i < j && !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom)));
            return { nomes: v.map(x => x[0]), bate }; })()""")
        dentro_mapa = pg.evaluate("""(() => { const m = document.getElementById('map').getBoundingClientRect();
            return [...document.querySelectorAll('.rotulo')].filter(e => e.style.visibility !== 'hidden').every(e => { const r = e.firstChild.getBoundingClientRect(); return r.left >= m.left && r.right <= m.right && r.top >= m.top && r.bottom <= m.bottom; }); })()""")
        check(dentro_mapa, f"{modo}: nenhum rótulo de cidade sai da área do mapa")
        check(len(rot["nomes"]) >= 5 and "João Pessoa" in rot["nomes"] and not rot["bate"] and pg.locator(".leaflet-control-scale-line").count() == 1 and "Fonte:" in pg.inner_text(".fonte-mapa"),
              f"{modo}: rótulos das cidades-polo sem sobreposição ({rot['nomes']}), barra de escala e fonte no mapa")
        # Enquadramento: com a ficha aberta, o estado inteiro fica na área livre, ao lado da ficha
        pg.evaluate(f"location.hash = '#mapa-{SOUSA}'"); pg.wait_for_timeout(1100)
        enq = pg.evaluate("PAINEL.enquadramento()")
        borda_ficha = pg.evaluate("document.getElementById('painel').getBoundingClientRect().left - document.getElementById('map').getBoundingClientRect().left")
        check(enq["x0"] >= 0 and enq["x1"] <= borda_ficha and enq["y0"] >= 0 and enq["y1"] <= enq["h"],
              f"{modo}: com a ficha aberta o estado inteiro aparece ao lado dela (estado até x={enq['x1']:.0f}; ficha começa em {borda_ficha:.0f})")
        leg_ok = pg.evaluate("""(() => { const l = document.getElementById('leg').getBoundingClientRect(), f = document.getElementById('painel').getBoundingClientRect();
            return l.width > 0 && l.height > 0 && (l.right <= f.left || l.left >= f.right); })()""")
        foco = pg.evaluate("[document.activeElement.tagName, getComputedStyle(document.activeElement).outlineStyle]")
        check(leg_ok and foco == ["H2", "none"], f"{modo}: com a ficha aberta a legenda continua visível ao lado; título da ficha com foco e sem moldura ({foco})")
        if modo == "http":
            pg.screenshot(path=str(CAP / "mapa_ficha_enquadrada.png"))
        pg.evaluate("location.hash = '#mapa'"); pg.wait_for_timeout(400)
        # Ver estado inteiro, limite de arraste e zoom
        pg.evaluate("PAINEL.limitesMapa(); 0"); pg.click(".leaflet-control-zoom-in"); pg.click(".leaflet-control-zoom-in"); pg.wait_for_timeout(500)
        pg.click("#verEstado"); pg.wait_for_timeout(700)
        enq2 = pg.evaluate("PAINEL.enquadramento()")
        check(enq2["x0"] >= 0 and enq2["x1"] <= enq2["w"] and enq2["y0"] >= 0 and enq2["y1"] <= enq2["h"], f"{modo}: botão Ver estado inteiro volta a mostrar a Paraíba toda")
        # Limites das regiões: ligar/desligar
        pg.uncheck("#verRegioes"); pg.wait_for_timeout(200)
        desl = pg.evaluate("[...document.querySelectorAll('.leaflet-regioes-pane path')].every(p => p.getAttribute('stroke-opacity') === '0')")
        pg.check("#verRegioes"); pg.wait_for_timeout(200)
        lig = pg.evaluate("[...document.querySelectorAll('.leaflet-regioes-pane path')].filter(p => p.getAttribute('stroke-opacity') !== '0').length")
        check(desl and lig == 16, f"{modo}: limites das 16 regiões de saúde ligam e desligam")
        # Região de saúde: recorta mapa, ranking e tabela; média da região na legenda = view
        RG = "25016"; dentro = {c for c, r in MUNREG.items() if r == RG}; rg = REGREF[(RG, "all", "total")]
        largura = "(() => { const b = PAINEL.limitesMapa(); return b.getEast() - b.getWest(); })()"
        z0 = pg.evaluate(largura)
        pg.select_option("#reg", RG); pg.wait_for_timeout(500)
        rk = pg.evaluate("[...document.querySelectorAll('#rk a')].map(a => a.getAttribute('href').slice(6))")
        z1 = pg.evaluate(largura)
        if modo == "http":
            pg.screenshot(path=str(CAP / "regiao_saude_filtro.png"))
        destaque = pg.evaluate("[...document.querySelectorAll('.leaflet-regioes-pane path')].filter(p => p.getAttribute('stroke-width') === '3.2').length")
        check(destaque == 1, f"{modo}: limite da região escolhida destacado ({destaque})")
        pg.click("#verTabela"); pg.wait_for_timeout(300)
        lin_reg = pg.evaluate("[...document.querySelectorAll('#maptab tbody tr[data-c]')].map(tr => tr.dataset.c)")
        pg.click("#verTabela"); pg.wait_for_timeout(200)
        check(rk and set(rk) <= dentro and set(lin_reg) == dentro and len(lin_reg) == len(dentro) and z1 < z0 and rg["nome"] in pg.inner_text("#mapatitulo")
              and f"Média da {rg['nome']}: {fmt(rg['taxa'], 1)}" in pg.text_content("#leg"),
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
        # O que olhar primeiro: frase-resumo calculada, depois os 5 indicadores, depois os contextos
        resumo = pg.inner_text("#painel .resumo")
        ordem = pg.evaluate("[...document.querySelectorAll('#painel > .resumo, #painel details.sec')].map(e => e.dataset.sec || 'resumo')")
        check(resumo == "Sousa registra cerca de 1/10 das notificações esperadas para o seu número de mulheres. Se seguisse a média da Paraíba, teria cerca de 175 casos em 6 anos; registrou 15."
              and ordem == ["resumo", "ind", "faixa", "ano", "local", "rede"]
              and pg.locator("#painel details[data-sec=ind] .ind5 .it").count() == 5,
              f"{modo}: ficha começa pela frase-resumo calculada ({resumo!r}) e segue indicadores, depois contextos ({ordem})")
        # Frase-resumo para os 223 municípios em todos os tipos e períodos: sem "que o estado", sem "do esperado" solto, casos sempre inteiros
        frases = pg.evaluate("""(() => { const per = ['all'].concat(PAINEL.ANOS.map(String)), r = [];
            PAINEL.F.forEach(f => ['total', 'fisica', 'psicologica', 'sexual'].forEach(t => per.forEach(p => r.push([f.properties.cod, f.properties.nome, t, p, PAINEL.resumo(f.properties.cod, t, p)])))); return r; })()""")
        ruins = [x for x in frases if "que o estado" in x[4] or "do estado" in x[4] or re.search(r"do esperado(?! para)", x[4]) or re.search(r"\d+,\d+ casos?\b", x[4])
                 or not x[4].startswith(x[1] + " ") or "Paraíba" not in x[4]]
        n_total = sum(1 for x in frases if x[2] == "total" and x[3] == "all")
        sume = pg.evaluate(f"PAINEL.resumo('{SUME}', 'total', 'all')")
        perto = next(c for (c, per, t), v in REF.items() if per == "all" and t == "total" and v["casos"] >= 10 and 0.8 <= v["oe"] < 1.25)
        frase_perto = pg.evaluate(f"PAINEL.resumo('{perto}', 'total', 'all')")
        check(not ruins and n_total == TOTAL_MUNICIPIOS and len(frases) == TOTAL_MUNICIPIOS * 4 * 7
              and sume.startswith("Sumé registra 4,6 vezes mais notificações que a média da Paraíba, considerando o número de mulheres.")
              and "registra notificações perto da média da Paraíba" in frase_perto,
              f"{modo}: frase-resumo gerada para os 223 municípios × 4 tipos × 7 períodos ({len(frases)} frases), {len(ruins)} com 'que o estado', 'do esperado' solto ou casos com decimal {ruins[:2]}; Sumé: {sume[:60]!r}")
        if modo == "http":
            # tela mais alta e indicador "Comparação com a média": a captura mostra a frase-resumo e os indicadores da ficha
            tam = pg.viewport_size; pg.set_viewport_size({"width": 1366, "height": 1180}); pg.select_option("#ind", "oe")
            for cod, arq in ((SUME, "ficha_resumo_sume"), (SOUSA, "ficha_resumo_sousa"), (JP, "ficha_resumo_joao_pessoa")):
                pg.evaluate(f"location.hash = '#mapa-{cod}'"); pg.wait_for_timeout(800); pg.screenshot(path=str(CAP / f"{arq}.png"))
            pg.select_option("#ind", "taxa"); pg.set_viewport_size(tam)
            pg.evaluate(f"location.hash = '#mapa-{SOUSA}'"); pg.wait_for_timeout(700)
        # Faixa etária: alternância Casos | Taxa por 100 mil/ano, com a taxa do estado como referência e aviso de valor instável
        pg.click("#painel [data-fx=taxa]"); pg.wait_for_timeout(200)
        fxt = pg.inner_text("#painel .fxcorpo")
        ok_fx = all(fmt(FXREF[(SOUSA, i)][1], 1) + (" *" if FXREF[(SOUSA, i)][0] < 10 else "") in fxt for i in range(1, 11))
        refs = pg.evaluate("[...document.querySelectorAll('#painel .fxcorpo .ref')].map(e => e.title)")
        check(ok_fx and "valor instável" in fxt and "Ignorada" in fxt and "sem taxa" in fxt and refs == [f"Paraíba: {fmt(FXEST[i], 1)}" for i in range(1, 11)]
              and pg.get_attribute("#painel [data-fx=taxa]", "aria-pressed") == "true",
              f"{modo}: ficha de Sousa com taxa por faixa = view, taxa do estado como referência e aviso de valor instável")
        if modo == "http":
            pg.locator("#painel .fxcorpo").scroll_into_view_if_needed(); pg.screenshot(path=str(CAP / "ficha_faixa_taxa.png"))
        pg.click("#painel [data-fx=casos]"); pg.wait_for_timeout(200)
        check("Faixa mais atingida" in pg.inner_text("#painel") and "%" in pg.inner_text("#painel .fxcorpo"), f"{modo}: botão Casos volta à contagem por faixa")
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
                ok_cmp &= abs(num_br(tab["linhas"]["Comparação com a média da Paraíba (1 = igual)"][i]) - rr["oe"]) <= 0.005 + 1e-9
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
        # Taxa por faixa do painel = view, em todos os municípios e faixas
        calc_fx = pg.evaluate("(() => { const P = PAINEL, out = []; for (const f of P.F) for (let i = 0; i < 10; i++) out.push([f.properties.cod, i + 1, P.taxaFaixa(f.properties, i)]); return out; })()")
        dif = [x for x in calc_fx if abs(x[2] - FXREF[(x[0], x[1])][1]) > TOL]
        est_fx = pg.evaluate("[...Array(10).keys()].map(i => PAINEL.taxaFaixaEstado(i))")
        check(len(calc_fx) == len(FXREF) == TOTAL_MUNICIPIOS * 10 and not dif and all(abs(est_fx[i] - FXEST[i + 1]) <= TOL for i in range(10)),
              f"{modo}: taxa por faixa do painel × view em {len(calc_fx)} município × faixa ({len(dif)} divergentes) e no estado")
        # Local de atendimento: % do painel = view (todos os municípios); ficha com número e %; aviso de valor instável
        calc_loc = pg.evaluate("(() => PAINEL.F.flatMap(f => [0, 1, 2].map(k => [f.properties.cod, k + 1, PAINEL.pctLocal(f.properties.local, k)])))()")
        dif = [x for x in calc_loc if (x[2] is None) != (LOCREF[(x[0], x[1])][2] is None) or (x[2] is not None and abs(x[2] - LOCREF[(x[0], x[1])][2]) > TOL)]
        check(len(calc_loc) == TOTAL_MUNICIPIOS * 3 and not dif, f"{modo}: % do local de atendimento × view em {len(calc_loc)} município × categoria ({len(dif)} divergentes)")
        PEQ_LOC = min(c for (c, k), v in LOCREF.items() if k == 1 and 0 < v[1] < 10)
        for c in [SOUSA, PEQ_LOC]:
            pg.evaluate(f"location.hash = '#mapa-{c}'"); pg.wait_for_timeout(500)
            txt = pg.inner_text("#painel .local")
            ok_l = all(f"{LOCREF[(c, k)][0]} " in txt and npct(LOCREF[(c, k)][2]) in txt for k in (1, 2, 3))
            instavel = "mudam muito com um caso" in txt
            check(ok_l and instavel == (LOCREF[(c, 1)][1] < 10) and "O dado não diz o motivo" in txt and pg.locator("#painel .local .barra100 span").count() >= 1,
                  f"{modo}: ficha ({REF[(c, 'all', 'total')]['nome']}) mostra onde as mulheres foram atendidas, com número, % e aviso de instabilidade quando < 10 casos")
            if modo == "http" and c == SOUSA:
                pg.locator("#painel .local").scroll_into_view_if_needed(); pg.screenshot(path=str(CAP / "ficha_local_atendimento.png"))
        # Bloco MUNIC 2023 na ficha = arquivo bruto, em 10 municípios sorteados (semente 42)
        TEXTO = {"Sim": "Sim", "Não": "Não", "-": "Sem dado"}
        dif_rede = []
        for c in random.Random(42).sample(sorted(REDE_BRUTO), 10):
            pg.evaluate(f"location.hash = '#mapa-{c}'"); pg.wait_for_timeout(500)
            itens = pg.evaluate("[...document.querySelectorAll('#painel .rede li')].map(li => [li.dataset.k, li.dataset.v, li.querySelector('b').textContent, li.querySelector('.ic').textContent])")
            esperado = [[k, REDE_BRUTO[c][k], TEXTO[REDE_BRUTO[c][k]]] for k in COLS_REDE]
            if [i[:3] for i in itens] != esperado or any(not i[3] for i in itens):
                dif_rede.append(c)
        nota = pg.inner_text("#painel .rede .nota")
        check(not dif_rede and nota == "Informação declarada pela prefeitura em 2023. Serviços criados depois não aparecem.",
              f"{modo}: bloco MUNIC 2023 da ficha igual ao bruto em 10 municípios sorteados, com ícone, texto e nota fixa ({dif_rede})")
        if modo == "http":
            pg.locator("#painel .rede").scroll_into_view_if_needed(); pg.screenshot(path=str(CAP / "ficha_rede_munic.png"))
        # Tabela da Análise (arredondamento) e CSV
        pg.evaluate("location.hash = '#analise'"); pg.wait_for_timeout(300)
        # Leituras prontas: contextos calculados dos dados, cada leitura com evidência e pergunta para a gestão
        concl = pg.inner_text("#concl")
        i_max = max(FXEST, key=FXEST.get)
        rot_max = {1: "Menos de 1", 2: "1 a 4", 3: "5 a 9", 4: "10 a 14", 5: "15 a 19", 6: "20 a 29", 7: "30 a 39", 8: "40 a 49", 9: "50 a 59", 10: "60 ou mais"}[i_max]
        n_serv = {k: sum(1 for x in REDE_BRUTO.values() if x[k] == "Sim") for k in COLS_REDE}
        check(f"Em taxa, a faixa etária mais atingida é {rot_max} anos." in concl and fmt(FXEST[i_max], 1) in concl
              and f"{npct(LOCEST[1][1])} das notificações foram feitas na região de saúde onde a mulher mora" in concl
              and all(f"{n} declaram" in concl for n in n_serv.values())
              and pg.locator("#concl li").count() == pg.locator("#concl li .perg").count() >= 10,
              f"{modo}: leituras prontas dos contextos (faixa {rot_max}, local, MUNIC) calculadas, cada uma com pergunta para a gestão")
        graf = pg.evaluate("""(() => { const ac = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim().toLowerCase();
            const linhas = [...document.querySelectorAll('#g-serie polyline')], dl = linhas.filter(l => l.dataset.destaque);
            const rot = [...document.querySelectorAll('#g-serie text.val.destaque')].map(t => t.textContent);
            const tipo = [...document.querySelectorAll('#g-tipo rect[data-destaque]')].map(r => r.dataset.t);
            const antigas = ['#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#3987e5', '#d95926', '#199e70', '#d55181'];
            const usadas = [...document.querySelectorAll('#v-analise svg [fill], #v-analise svg [stroke]')].flatMap(e => [e.getAttribute('fill'), e.getAttribute('stroke')]).filter(Boolean).map(x => x.toLowerCase());
            return { n: linhas.length, dest: dl.length, cor: dl[0] && dl[0].getAttribute('stroke').toLowerCase(), ac, rot, tipo, antigas: usadas.filter(x => antigas.includes(x)).length }; })()""")
        check(graf["n"] == 4 and graf["dest"] == 1 and graf["cor"] == graf["ac"] and graf["rot"] == ["Sexual"] and len(graf["tipo"]) == 1 and graf["tipo"][0].startswith("Sexual") and graf["antigas"] == 0,
              f"{modo}: gráficos em cinza com uma série destacada no azul-petróleo (Sexual) e sem as 4 cores genéricas")
        frase = pg.inner_text("#localfrase")
        esperada = (f"Das mulheres notificadas, {npct(LOCEST[1][1])} foram atendidas na própria região de saúde, {npct(LOCEST[2][1])} em outra região da Paraíba "
                    f"e {npct(LOCEST[3][1])} fora da Paraíba ({LOCEST[3][0]} casos).")
        check(frase == esperada, f"{modo}: frase do estado na Análise igual ao cálculo do banco ({frase!r})")
        if modo == "http":
            pg.locator("#g-local").scroll_into_view_if_needed(); pg.screenshot(path=str(CAP / "analise_local_atendimento.png"))
        pg.click("#fxAnalise [data-fxa=taxa]"); pg.wait_for_timeout(200)
        rot = pg.get_attribute("#g-faixa svg", "aria-label") or ""
        check(all(fmt(FXEST[i], 1) in rot for i in range(1, 11)) and "Paraíba: " + fmt(EST[("all", "total")], 1) in rot and "não tem taxa" in pg.inner_text("#fxdesc"),
              f"{modo}: Análise mostra a taxa por faixa do estado com a taxa geral como referência")
        if modo == "http":
            pg.locator("#g-faixa").scroll_into_view_if_needed(); pg.screenshot(path=str(CAP / "analise_faixa_taxa.png"))
        pg.click("#fxAnalise [data-fxa=casos]"); pg.wait_for_timeout(200)
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

    # ======================= Sobre o painel (1ª visita), tour e estados de carga/erro =======================
    ctx = ctx_puro(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page(); erros_s = []; ouvir(pg, erros_s)
    abrir(pg, MODOS["http"])
    txt_sobre = pg.inner_text("#sobre") if pg.evaluate("document.getElementById('sobre').open") else ""
    passos_sobre = pg.locator("#sobre ol.passos li").count() if txt_sobre else 0
    check(all(x in txt_sobre.lower() for x in ["como usar", "casos notificados", "taxa por 100 mil mulheres por ano", "tipos de violência", "faixa etária",
                                                "comparação com a média da paraíba", "observado ÷ esperado", "como ler", "menos de 10 casos", "fontes"]) and passos_sobre == 3
          and "não o total de casos que ocorrem" in pg.inner_text("header .nota-topo") and pg.locator("#carregando").count() == 0,
          "1ª visita: Sobre o painel abre sozinho com uso em 3 passos, 5 indicadores, como ler e fontes; o aviso de notificação fica sob o título (e o de carregamento some)")
    pg.screenshot(path=str(CAP / "sobre_o_painel.png"))
    pg.click("#sobreComecar"); pg.reload(); pg.wait_for_function("window.PAINEL !== undefined"); pg.wait_for_timeout(300)
    check(not pg.evaluate("document.getElementById('sobre').open"), "Sobre o painel não volta depois de fechado (localStorage)")
    pg.click("#abrirSobre"); pg.wait_for_timeout(150)
    check(pg.evaluate("document.getElementById('sobre').open"), "botão Sobre o painel reabre a tela")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
    # Tour de 6 passos: mapa da taxa, observado ÷ esperado, ficha de Sousa, faixa em taxa, Análise, Como calcular
    ESTADO_TOUR = """(() => { const b = document.querySelector('#painel [data-fx=taxa]');
        return [document.getElementById('tourPasso').textContent, document.getElementById('tourT').textContent, location.hash,
                document.getElementById('ind').value, b ? b.getAttribute('aria-pressed') : '']; })()"""
    pg.click("#abrirTour"); pg.wait_for_timeout(400)
    passos = []
    for k in range(6):
        passos.append(pg.evaluate(ESTADO_TOUR))
        if k == 3:
            pg.screenshot(path=str(CAP / "tour_passo4.png"))
        if k < 5:
            pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(800)
    pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(400)
    volta = pg.evaluate("location.hash")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    check([x[0] for x in passos] == [f"Passo {i} de 6" for i in range(1, 7)] and passos[0][2] == "#mapa" and passos[0][3] == "taxa" and passos[1][3] == "oe"
          and passos[2][2] == "#mapa-" + SOUSA and passos[3][4] == "true" and passos[4][2] == "#analise" and passos[5][2] == "#como-calcular"
          and volta == "#analise" and pg.evaluate("document.getElementById('tour').hidden") and pg.evaluate("document.activeElement.id") == "abrirTour" and not erros_s,
          f"tour: 6 passos na ordem combinada, setas e Esc (foco volta ao botão) {[x[1] for x in passos]}")
    sem_travessao = pg.evaluate("!(document.querySelector('main').textContent + document.getElementById('sobre').textContent + document.getElementById('tour').textContent + document.querySelector('header').textContent).includes('—')")
    check(sem_travessao, "textos das 3 telas, do Sobre e do Tour sem travessão (—)")
    topo = pg.evaluate("[...document.querySelectorAll('header .acoes .btn')].map(b => getComputedStyle(b).borderTopStyle + '/' + getComputedStyle(b).backgroundColor)")
    estado = pg.evaluate("[document.getElementById('verEstado').getAttribute('aria-label'), document.getElementById('verEstado').getBoundingClientRect().width]")
    check(all(t.startswith("none/") for t in topo) and estado[0] == "Ver a Paraíba inteira" and estado[1] <= 46,
          f"topo com Sobre, Tour e Copiar link como links de texto; 'Ver a Paraíba inteira' como botão de ícone com rótulo acessível ({estado})")
    ctx.close()
    # chegar por link de ficha não abre o Sobre
    ctx = ctx_puro(viewport={"width": 1366, "height": 768}); pg = ctx.new_page()
    abrir(pg, MODOS["http"] + "#mapa-" + SOUSA)
    check(not pg.evaluate("document.getElementById('sobre').open"), "link direto para a ficha não abre o Sobre na 1ª visita")
    ctx.close()
    # erro: sem dados.json e dados.js, mensagem útil com o que fazer
    sem = pathlib.Path(tempfile.mkdtemp(prefix="websig_semdados_"))
    for parte in ["index.html", "css", "js", "vendor"]:
        origem = WEB / parte
        if origem.is_dir():
            shutil.copytree(origem, sem / parte)
        else:
            shutil.copy(origem, sem / parte)
    ctx = nav.new_context(); pg = ctx.new_page(); pg.goto((sem / "index.html").as_uri()); pg.wait_for_timeout(1500)
    err_txt = pg.inner_text("main")
    check("Não foi possível carregar os dados do painel" in err_txt and "atualizar.bat" in err_txt and pg.locator(".erro button").count() == 1 and pg.locator("#carregando").count() == 0,
          "estado de erro: sem os arquivos de dados, a tela explica o problema e o que fazer")
    if NAV == "chrome":
        pg.screenshot(path=str(CAP / "estado_erro.png"))
    ctx.close(); shutil.rmtree(sem, ignore_errors=True)

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
            rot_base = f"{nome}_{'claro' if tema == 'light' else 'escuro'}"
            pg = ctx.new_page(); erros_t = []; ouvir(pg, erros_t)
            if nome in ("1366", "celular"):
                abrir(pg, MODOS["http"]); pg.wait_for_timeout(600)
                fundo = pg.evaluate("""(() => { const lum = c => { const v = c.match(/[\\d.]+/g).slice(0, 3).map(Number).map(x => x / 255).map(x => x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
                    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
                    return [lum(getComputedStyle(document.querySelector('.leaflet-container')).backgroundColor), lum(getComputedStyle(document.getElementById('leg')).backgroundColor)]; })()""")
                escuro = tema == "dark"
                pagina = pg.evaluate("""(() => { const v = getComputedStyle(document.body).backgroundColor.match(/[\\d.]+/g).slice(0, 3).map(Number).map(x => x / 255).map(x => x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
                    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; })()""")
                check(all(x > 0.6 for x in fundo) and ((pagina < 0.1) if escuro else (pagina > 0.6)),
                      f"{rot_base}: canvas claro nos dois temas (fundo do mapa e da legenda {[round(x, 2) for x in fundo]}); a interface ao redor segue o tema ({round(pagina, 2)})")
                if not cel:
                    # legenda compacta: sem rolagem, uma linha por classe, explicações recolhidas, nada sobre os botões de zoom nem sobre o estado
                    for ind in ["taxa", "oe"]:
                        pg.select_option("#ind", ind); pg.wait_for_timeout(400)
                        g = pg.evaluate(GEOM)
                        check(g["rol"] <= 1 and max(g["linhas"]) <= 24 and g["ler"] and g["est"][0] >= g["mapa"][0] and g["est"][2] <= g["mapa"][2] and g["est"][3] <= g["mapa"][3] and not bate(g["leg"], g["ctl"]) and not g["toca"]["leg"] and not g["toca"]["ctl"],
                              f"{rot_base} ({ind}): legenda sem rolagem, uma linha por classe (alturas {g['linhas']}), 'Como ler' recolhido, sem cobrir zoom nem estado")
                    pg.click("#leg .leg-tog"); pg.wait_for_timeout(200)
                    fechada = pg.evaluate("getComputedStyle(document.querySelector('#leg .leg-corpo')).display")
                    pg.click("#leg .leg-tog"); pg.wait_for_timeout(200)
                    check(fechada == "none" and pg.evaluate("getComputedStyle(document.querySelector('#leg .leg-corpo')).display") != "none", f"{rot_base}: botão recolhe e mostra a legenda inteira")
                    pg.click("#leg details.leg-ler summary"); pg.wait_for_timeout(300)
                    g = pg.evaluate(GEOM)
                    check("Esperado:" in pg.inner_text("#leg") and not g["toca"]["leg"] and not bate(g["leg"], g["ctl"]),
                          f"{rot_base}: 'Como ler esta legenda' abre as explicações e o mapa se reenquadra sem nada sobre o estado")
                    pg.click("#leg details.leg-ler summary"); pg.wait_for_timeout(300)
                    pg.select_option("#ind", "taxa"); pg.wait_for_timeout(300)
                if cel:
                    fechada = pg.evaluate("getComputedStyle(document.querySelector('#leg .leg-corpo')).display")
                    pg.click("#leg .leg-tog"); pg.wait_for_timeout(200)
                    aberta = pg.evaluate("getComputedStyle(document.querySelector('#leg .leg-corpo')).display")
                    pg.wait_for_timeout(300); g = pg.evaluate(GEOM)
                    inteiro = g["est"][0] >= g["mapa"][0] and g["est"][2] <= g["mapa"][2] and g["est"][1] >= g["mapa"][1] and g["est"][3] <= g["mapa"][3]
                    check(fechada == "none" and aberta != "none" and inteiro,
                          f"{rot_base}: legenda recolhível no celular ({fechada} → {aberta}); aberta, o estado continua inteiro no mapa")
                    pg.click("#leg .leg-tog"); pg.wait_for_timeout(300)
                for ind in ["taxa", "oe", "casos"]:
                    pg.select_option("#ind", ind); pg.wait_for_timeout(400)
                    pg.screenshot(path=str(CAP / f"{rot_base}_mapa_{ind}.png"))
                pg.select_option("#ind", "taxa")
            if nome in ("1366", "celular"):
                abrir(pg, MODOS["http"] + "#mapa-" + SUME); pg.wait_for_timeout(900)
                g = pg.evaluate(GEOM)
                if not cel:
                    util = g["ficha"][0] - g["leg"][2]
                    larg = g["est"][2] - g["est"][0]
                    check(larg >= 0.6 * util and not any(g["toca"][k] for k in ("leg", "ficha", "ctl", "tit")) and g["est"][2] <= g["ficha"][0] and g["rol"] <= 1,
                          f"{rot_base}: ficha de Sumé aberta, estado com {larg:.0f} px = {100 * larg / util:.0f}% da largura útil entre a legenda e a ficha ({util:.0f} px; mínimo 60%), sem nada sobreposto")
                pg.screenshot(path=str(CAP / f"{rot_base}_ficha_sume.png"))
            abrir(pg, MODOS["http"] + "#mapa-" + SOUSA); pg.wait_for_timeout(800)
            rot = f"{nome}_{'claro' if tema == 'light' else 'escuro'}"
            sem_rol = pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            secs = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#painel details.sec')].map(d => [d.dataset.sec, d.open]))")
            if cel:   # no celular a ficha fica embaixo: o estado inteiro tem de caber acima dela
                eq = pg.evaluate("PAINEL.enquadramento()")
                topo_ficha = pg.evaluate("document.getElementById('painel').getBoundingClientRect().top - document.getElementById('map').getBoundingClientRect().top")
                check(eq["y0"] >= 0 and eq["y1"] <= topo_ficha and eq["x0"] >= 0 and eq["x1"] <= eq["w"],
                      f"{nome}_{tema}: com a ficha aberta, o estado inteiro aparece acima dela (até y={eq['y1']:.0f}; ficha em {topo_ficha:.0f})")
            esperado_secs = {"ind": True, "faixa": False, "ano": False, "local": False, "rede": False} if cel else {k: True for k in ["ind", "faixa", "ano", "local", "rede"]}
            check(secs == esperado_secs, f"{nome}_{tema}: seções da ficha {'recolhidas no celular (só os indicadores abertos)' if cel else 'abertas na tela grande'} {secs}")
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
