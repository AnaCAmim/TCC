"""Teste-piloto de usabilidade e acessibilidade com Playwright (Chrome instalado).
- Tarefas T1–T5 do plano de avaliação, cada uma partindo da página inicial: conta as ações (clique, escolha numa lista,
  digitar + Enter) e confere a resposta na tela contra a resposta calculada direto do web/dados.json. Limite: 4 ações.
- Contraste WCAG 2.1 AA das cores do tema claro e escuro; paleta do mapa sob simulação de daltonismo (Machado et al., 2009);
  celular 320 px sem rolagem lateral; mapa visível sem rolar no celular; botões de zoom com 44 px; controles com nome.
- Grava capturas/piloto_tarefas.json e capturas/piloto_T*.png. Confere se docs/teste_usuarios/respostas.json está atualizado.
Uso: python testes/testar_usabilidade.py   (requer: pip install playwright)"""
import csv
import functools
import http.server
import io
import json
import math
import pathlib
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from respostas_tarefas import respostas_certas  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parents[1]
# Navegador: Chrome instalado (padrão) ou os do Playwright: python testes/<teste>.py --navegador firefox | webkit | chromium
NAV = sys.argv[sys.argv.index("--navegador") + 1] if "--navegador" in sys.argv else "chrome"


def lancar(pw):
    return pw.chromium.launch(channel="chrome", headless=True) if NAV == "chrome" else getattr(pw, NAV).launch(headless=True)


def movel(on=True):
    """Opções de celular. O Firefox do Playwright não emula is_mobile: lá só a tela pequena e o toque."""
    return {"has_touch": on, **({} if NAV == "firefox" else {"is_mobile": on})}
WEB = RAIZ / "web"
CAP = RAIZ / "capturas" if NAV == "chrome" else pathlib.Path(tempfile.mkdtemp(prefix=f"websig_{NAV}_"))
RESPOSTAS = RAIZ / "docs" / "teste_usuarios" / "respostas.json"
CAP.mkdir(exist_ok=True)
MAX_ACOES = 4
falhas, ok = [], []


def check(cond, msg):
    (ok if cond else falhas).append(msg)


def fmt(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


R = respostas_certas(json.loads((WEB / "dados.json").read_text(encoding="utf-8")))
if RESPOSTAS.exists():
    check(json.loads(RESPOSTAS.read_text(encoding="utf-8")) == R, "material do teste: docs/teste_usuarios/respostas.json igual ao dados.json atual (senão rode testes/gerar_material_teste.py)")


# ---------------- servidor local ----------------
class Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(WEB)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
INICIO = f"http://127.0.0.1:{srv.server_address[1]}/index.html"



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


class Tarefa:
    """Registra cada ação do usuário simulado."""
    def __init__(self, pg):
        self.pg, self.acoes = pg, []

    def clicar(self, sel, desc):
        self.pg.click(sel); self.acoes.append(desc); self.pg.wait_for_timeout(350)

    def escolher(self, sel, valor, desc):
        self.pg.select_option(sel, valor); self.acoes.append(desc); self.pg.wait_for_timeout(350)

    def digitar_enter(self, sel, texto, desc):
        self.pg.click(sel); self.pg.keyboard.type(texto); self.pg.keyboard.press("Enter"); self.acoes.append(desc); self.pg.wait_for_timeout(800)


def nova(nav, **kw):
    ctx = nav.new_context(viewport={"width": 1366, "height": 768}, accept_downloads=True, **kw)
    pg = ctx.new_page(); erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto(INICIO); pg.wait_for_function("window.PAINEL !== undefined"); pg.wait_for_selector("path.leaflet-interactive")
    return ctx, pg, erros


registro = {}
with sync_playwright() as p:
    nav = lancar(p)
    ctx_puro = visita_repetida(nav)

    # T1: os 3 municípios de menor observado ÷ esperado com pelo menos 10 casos
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    t.escolher("#ind", "oe", "Indicador: Observado ÷ esperado")
    t.clicar("#rk-menores", "Ranking: 10 menores")
    vistos = pg.evaluate("[...document.querySelectorAll('#rk a')].slice(0, 3).map(a => a.getAttribute('href').slice(6))")
    texto = pg.inner_text("#rk")
    certo = [m["cod"] for m in R["T1"]["municipios"]]
    check(vistos == certo and all(fmt(m["oe"], 2) in texto for m in R["T1"]["municipios"]), f"T1: 3 menores O/E com 10+ casos na tela = dados.json ({vistos} × {certo})")
    pg.screenshot(path=str(CAP / "piloto_T1.png")); registro["T1"] = t.acoes; check(not erros, f"T1: sem erros {erros[:1]}"); ctx.close()

    # T2: ficha de Sousa, acima ou abaixo da média do estado
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    t.digitar_enter("#busca", "Sousa", "Busca: digitar 'Sousa' e Enter")
    ficha = pg.inner_text("#painel")
    check(fmt(R["T2"]["taxa_sousa"], 1) in ficha and f"Média do estado: {fmt(R['T2']['taxa_estado'], 1)}" in ficha
          and "Notifica menos que a média do estado" in ficha and R["T2"]["resposta"] == "abaixo", "T2: ficha de Sousa mostra taxa, média do estado e a leitura 'notifica menos'")
    pg.screenshot(path=str(CAP / "piloto_T2.png")); registro["T2"] = t.acoes; check(not erros, f"T2: sem erros {erros[:1]}"); ctx.close()

    # T3: faixa etária mais atingida em Campina Grande
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    t.digitar_enter("#busca", "Campina Grande", "Busca: digitar 'Campina Grande' e Enter")
    frase = pg.inner_text("#painel .fxtop") if pg.locator("#painel .fxtop").count() else ""
    rot = [f.replace("-", " a ") + " anos" for f in R["T3"]["faixas"]]
    check(all(r in frase for r in rot) and f"{R['T3']['pct']}%" in frase, f"T3: frase 'Faixa mais atingida' de Campina Grande = dados.json ({frase!r})")
    pg.locator("#painel .fxtop").scroll_into_view_if_needed()
    pg.screenshot(path=str(CAP / "piloto_T3.png")); registro["T3"] = t.acoes; check(not erros, f"T3: sem erros {erros[:1]}"); ctx.close()

    # T4: a violência sexual cresceu de 2019 a 2024?
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    t.clicar("button[data-v=analise]", "Aba Análise")
    concl = pg.inner_text("#concl")
    check(f"passou de {fmt(R['T4']['sexual_2019'], 0)} casos em 2019 para {fmt(R['T4']['sexual_2024'], 0)} em 2024" in concl
          and f"+{R['T4']['variacao_pct']}%" in concl, "T4: conclusões da Análise mostram a sexual de 2019 a 2024 = dados.json")
    pg.screenshot(path=str(CAP / "piloto_T4.png")); registro["T4"] = t.acoes; check(not erros, f"T4: sem erros {erros[:1]}"); ctx.close()

    # T5a: baixar a tabela
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    t.clicar("button[data-v=analise]", "Aba Análise")
    with pg.expect_download() as dl:
        t.clicar("#baixarCsv", "Baixar tabela (CSV)")
    texto = pathlib.Path(dl.value.path()).read_text(encoding="utf-8").lstrip("﻿")
    linhas = list(csv.reader(io.StringIO(texto), delimiter=";"))
    check(";".join(linhas[0]) == R["T5"]["cabecalho"] and len(linhas) - 1 == R["T5"]["linhas_csv"], f"T5: CSV baixado com {len(linhas) - 1} municípios")
    registro["T5 (baixar tabela)"] = t.acoes; check(not erros, f"T5a: sem erros {erros[:1]}"); ctx.close()

    # T5b: imprimir a ficha
    ctx, pg, erros = nova(nav); t = Tarefa(pg)
    pg.evaluate("window.__imp = 0; window.print = function () { window.__imp++; }; 0")
    t.digitar_enter("#busca", "Sousa", "Busca: digitar 'Sousa' e Enter")
    t.clicar("#painel [data-acao=imprimir]", "Imprimir ficha")
    check(pg.evaluate("window.__imp") == 1 and "Sousa" in pg.inner_text("#impressao"), "T5: ficha de Sousa enviada para impressão")
    registro["T5 (imprimir ficha)"] = t.acoes; check(not erros, f"T5b: sem erros {erros[:1]}"); ctx.close()

    # Primeira visita: "Sobre o painel" abre sozinho e fecha com 1 clique (soma 1 ação só na primeira vez)
    ctx = ctx_puro(viewport={"width": 1366, "height": 768}); pg = ctx.new_page()
    pg.goto(INICIO); pg.wait_for_function("window.PAINEL !== undefined")
    aberto = pg.evaluate("document.getElementById('sobre').open")
    t = Tarefa(pg); t.clicar("#sobreComecar", "Primeira visita: Começar (fecha Sobre o painel)")
    check(aberto and not pg.evaluate("document.getElementById('sobre').open"), "primeira visita: Sobre o painel abre e fecha com 1 clique")
    registro["Primeira visita (só uma vez)"] = t.acoes; ctx.close()

    for k, a in registro.items():
        check(len(a) <= MAX_ACOES, f"{k}: {len(a)} ações (limite {MAX_ACOES})")

    # Busca sem resultado dá retorno
    ctx, pg, erros = nova(nav)
    pg.click("#busca"); pg.keyboard.type("Xyzópolis"); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
    check("Nenhum município encontrado" in pg.inner_text("#buscaMsg"), "busca sem resultado avisa 'Nenhum município encontrado'")
    ctx.close()

    # ---------------- acessibilidade ----------------
    def rgb(h):
        h = h.strip().lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h
        return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    lum = lambda h: sum(k * lin(x) for k, x in zip((0.2126, 0.7152, 0.0722), rgb(h)))
    contraste = lambda a, b: (max(lum(a), lum(b)) + 0.05) / (min(lum(a), lum(b)) + 0.05)
    MACHADO = {"protanopia": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
               "deuteranopia": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
               "tritanopia": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]}

    def lab(v):
        X = (0.4124 * v[0] + 0.3576 * v[1] + 0.1805 * v[2]) / 0.95047
        Y = 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
        Z = (0.0193 * v[0] + 0.1192 * v[1] + 0.9505 * v[2]) / 1.08883
        f = lambda q: q ** (1 / 3) if q > 0.008856 else 7.787 * q + 16 / 116
        return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))

    def delta_vizinhos(cores, m=None):
        pts = []
        for c in cores:
            v = [lin(x) for x in rgb(c)]
            if m:
                v = [min(1, max(0, sum(m[i][j] * v[j] for j in range(3)))) for i in range(3)]
            pts.append(lab(v))
        return round(min(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)), 1)

    TOK = "(() => { const s = getComputedStyle(document.documentElement), o = {}; for (const n of ['--bg','--surface','--surface-2','--ink','--ink-2','--ink-3','--accent','--accent-soft','--on-accent','--warn-bg','--warn-ink','--q1','--q2','--q3','--q4','--q5','--d1','--d2','--d3','--d4','--d5']) o[n] = s.getPropertyValue(n).trim(); return o; })()"
    TEXTO = [("--ink", "--surface"), ("--ink-2", "--surface"), ("--ink-3", "--surface"), ("--ink-3", "--surface-2"), ("--ink-3", "--bg"),
             ("--ink-2", "--surface-2"), ("--on-accent", "--accent"), ("--accent", "--surface"), ("--warn-ink", "--warn-bg"), ("--ink", "--accent-soft")]
    acess = {}
    for tema in ["light", "dark"]:
        ctx, pg, erros = nova(nav, color_scheme=tema)
        tk = pg.evaluate(TOK)
        c = {f"{a} sobre {b}": round(contraste(tk[a], tk[b]), 2) for a, b in TEXTO}
        dal = {pal: {k: delta_vizinhos([tk[f"--{pal[0]}{i}"] for i in range(1, 6)], m) for k, m in [("normal", None)] + list(MACHADO.items())}
               for pal in ["q", "d"]}
        acess[tema] = {"contraste": c, "daltonismo_dE_min": {"sequencial": dal["q"], "divergente": dal["d"]}}
        check(min(c.values()) >= 4.5, f"contraste AA ({tema}): mínimo {min(c.values())}:1 (≥ 4,5)")
        # hachura do valor instável: lida do próprio mapa (cor da linha e opacidade de cada padrão), misturada à cor de fundo; contraste ≥ 3:1
        def mistura(base, op, fundo):
            return "#" + "".join(f"{round(op * int(base[i:i + 2], 16) + (1 - op) * int(fundo[i:i + 2], 16)):02x}" for i in (1, 3, 5))
        hach = {}
        for ind in ["taxa", "oe"]:
            pg.select_option("#ind", ind); pg.wait_for_timeout(300)
            for fundo, base, op in pg.evaluate("[...document.querySelectorAll('pattern[id^=hach-]')].map(p => [p.querySelector('rect').getAttribute('fill'), p.querySelector('line').getAttribute('stroke'), +p.querySelector('line').getAttribute('stroke-opacity')])"):
                hach[f"{ind} {fundo}"] = {"linha": base, "opacidade": op, "contraste": round(contraste(mistura(base, op, fundo), fundo), 2)}
        pg.select_option("#ind", "taxa")
        acess[tema]["hachura"] = hach
        check(len(hach) == 10 and min(v["contraste"] for v in hach.values()) >= 3,
              f"hachura ({tema}): contraste mínimo linha × cor {min(v['contraste'] for v in hach.values())}:1 (≥ 3), opacidade de {min(v['opacidade'] for v in hach.values())} a {max(v['opacidade'] for v in hach.values())}")
        # escalas: ordem de claridade preservada (normal, protanopia, deuteranopia, tritanopia e tons de cinza) e diferença mínima entre vizinhas
        def L_(cor, m=None):
            v = [lin(x) for x in rgb(cor)]
            if m: v = [min(1, max(0, sum(m[i][j] * v[j] for j in range(3)))) for i in range(3)]
            return lab(v)[0]
        ordem = {}
        for nome_pal, pal in [("sequencial", [tk[f"--q{i}"] for i in range(1, 6)]), ("divergente", [tk[f"--d{i}"] for i in range(1, 6)])]:
            for vis, m in [("normal", None)] + list(MACHADO.items()) + [("cinza", None)]:
                Ls = [round(L_(c, m), 1) for c in pal]   # em tons de cinza vale a claridade L* (a impressão preserva a luminância)
                ok_ordem = all(Ls[i] > Ls[i + 1] for i in range(4)) if nome_pal == "sequencial" else (Ls[0] < Ls[1] < Ls[2] > Ls[3] > Ls[4])
                ordem[f"{nome_pal} {vis}"] = {"L*": Ls, "ordem_ok": ok_ordem, "menor_passo_L": round(min(abs(Ls[i] - Ls[i + 1]) for i in range(4)), 1)}
        acess[tema]["ordem_claridade"] = ordem
        check(all(v["ordem_ok"] for v in ordem.values()), f"escalas ({tema}): ordem de claridade preservada em normal, protanopia, deuteranopia, tritanopia e tons de cinza")
        check(min(min(v.values()) for v in dal.values()) >= 10, f"daltonismo ({tema}): ΔE mínimo entre classes vizinhas {min(min(v.values()) for v in dal.values())} (≥ 10)")
        ctx.close()

    ctx = nav.new_context(viewport={"width": 320, "height": 640}, **movel())
    pg = ctx.new_page(); pg.goto(INICIO); pg.wait_for_function("window.PAINEL !== undefined"); pg.wait_for_selector("path.leaflet-interactive")
    cel = pg.evaluate("""(() => ({rol: document.documentElement.scrollWidth <= innerWidth + 1,
        mapa: Math.round(document.getElementById('map').getBoundingClientRect().top), alt: innerHeight,
        zoom: document.querySelector('.leaflet-control-zoom-in').getBoundingClientRect().height,
        semNome: [...document.querySelectorAll('button, a[href], input, select, [role=tab]')].filter(e => !((e.getAttribute('aria-label') || e.textContent || e.title || (e.labels && e.labels[0] && e.labels[0].textContent) || '').trim())).length}))()""")
    pg.screenshot(path=str(CAP / "piloto_celular_320.png"))
    acess["celular_320"] = cel
    check(cel["rol"], "celular 320 px: sem rolagem lateral (WCAG 1.4.10)")
    check(cel["zoom"] >= 44, f"celular: botões de zoom com {cel['zoom']:.0f} px (≥ 44)")
    check(cel["semNome"] == 0, f"controles sem nome acessível: {cel['semNome']}")
    ctx.close()
    ctx = nav.new_context(viewport={"width": 390, "height": 844}, **movel())
    pg = ctx.new_page(); pg.goto(INICIO); pg.wait_for_function("window.PAINEL !== undefined")
    cel390 = pg.evaluate("""(() => ({mapa: Math.round(document.getElementById('map').getBoundingClientRect().top), alt: innerHeight,
        rk: document.getElementById('rk').getBoundingClientRect().top > document.getElementById('map').getBoundingClientRect().top}))()""")
    acess["celular_390"] = cel390
    check(cel390["mapa"] < cel390["alt"] and cel390["rk"], f"celular 390×844: mapa começa na primeira tela ({cel390['mapa']} px de {cel390['alt']}) e o ranking fica abaixo dele")
    ctx.close()
    nav.close()
srv.shutdown()

(CAP / "piloto_tarefas.json").write_text(json.dumps({"acoes": registro, "respostas": R, "acessibilidade": acess}, ensure_ascii=False, indent=1), encoding="utf-8")
print("Piloto (ações por tarefa):")
for k, a in registro.items():
    print(f"  {k}: {len(a)} — " + " → ".join(a))
print(f"Teste de usabilidade ({NAV}): {len(ok)} verificações OK, {len(falhas)} falhas")
for f in falhas:
    print("  FALHA:", f)
sys.exit(1 if falhas else 0)
