/* mapa.js: tela Mapa (filtros, mapa coroplético, título com filtros, legenda, ranking, tabela do mapa,
   ficha do município com impressão, comparação de municípios). Usa só as fórmulas de calculo.js. */
"use strict";
window.WS = window.WS || {};
WS.mapa = (function () {
  const { $, nf, css, esc, semAc } = WS.util;
  const S = { ind: 'taxa', tipo: 'total', per: 'all', reg: '', sel: null, rk: 'maiores', tabela: false, fx: 'casos' };
  const MIN_CASOS = 10;   // abaixo disso a taxa e o observado ÷ esperado ficam instáveis
  const HINT = {
    taxa: 'Casos por ano a cada 100 mil mulheres. Compara municípios de tamanhos diferentes.',
    casos: 'Número de notificações. Mostra o volume de atendimento.',
    oe: 'Compara com o estado: 1 é igual; abaixo de 1, notifica menos; acima, mais.'
  };
  let C, map, camada, CL, porCamada = {}, ORDEM = [], naFrente = null, tip, ponteiro = 'mouse', dicaCod = null, dicaModo = null;
  const noRecorte = p => !S.reg || p.reg === S.reg;          // município dentro da região de saúde escolhida
  const nomeReg = cod => (C.REG[cod] ? C.REG[cod].nome : '');

  const valor = p => C.valor(p, S.ind, S.tipo, S.per);
  const casosSel = p => C.casos(p, S.tipo, S.per);
  const fmtValor = v => (S.ind === 'casos' ? nf(v) + (v === 1 ? ' caso' : ' casos') : S.ind === 'taxa' ? nf(v, 1) + ' por 100 mil/ano' : nf(v, 2) + '× o esperado');
  const filtrosTexto = () => C.NOME_IND[S.ind] + ' · ' + C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + (S.reg ? ' · ' + nomeReg(S.reg) : '');
  // tabindex="0" explícito: o Safari, por padrão, não passa por links com o Tab
  const linkCalc = ind => '<a href="#como-calcular" data-ind="' + ind + '" class="noprint" tabindex="0">como calcular</a>';

  /* ---------- classes de cor ---------- */
  function quantis(vals, k) { const v = [...vals].sort((a, b) => a - b), r = []; for (let i = 1; i < k; i++) r.push(v[Math.floor(i * v.length / k)]); return r; }
  function faixasRot(c, d, zero) {
    const r = [];
    if (zero) { r.push('Nenhum caso'); for (let i = 1; i < c.length; i++) r.push(nf(c[i - 1]) + ' a ' + nf(c[i] - 1)); }
    else { r.push('Menos de ' + nf(c[0], d)); for (let i = 1; i < c.length; i++) r.push(nf(c[i - 1], d) + ' a menos de ' + nf(c[i], d)); }
    r.push(nf(c[c.length - 1], d) + ' ou mais'); return r;
  }
  // Taxa: classes FIXAS por tipo de violência: quintis das taxas anuais positivas dos municípios de 2019 a 2024, arredondados
  // (múltiplos de 10; de 5 abaixo de 30). Valem para qualquer ano ou período, então as cores são comparáveis entre períodos.
  const limitesTaxa = {};
  function cortesTaxa(tipo) {
    if (limitesTaxa[tipo]) return limitesTaxa[tipo];
    const v = []; C.F.forEach(f => { const p = f.properties; p.casos[tipo].forEach(c => { if (c > 0) v.push(c / p.pop * 1e5); }); });
    const arred = x => (x >= 30 ? Math.round(x / 10) * 10 : Math.max(5, Math.round(x / 5) * 5));
    let c = quantis(v, 5).map(arred); c = c.filter((x, i) => i === 0 || x > c[i - 1]);
    return (limitesTaxa[tipo] = c);
  }
  const nfl = x => x.toLocaleString('pt-BR', { maximumFractionDigits: 2 });   // 0,5 · 1,25 · 40
  const rotCurto = c => ['menos de ' + nfl(c[0])].concat(c.slice(1).map((x, i) => nfl(c[i]) + ' a ' + nfl(x)), [nfl(c[c.length - 1]) + ' ou mais']);
  function classes() {
    if (S.ind === 'oe') { const c = [0.5, 0.8, 1.25, 2]; return { cort: c, cores: ['--d1', '--d2', '--d3', '--d4', '--d5'], rot: rotCurto(c), fixas: true }; }
    if (S.ind === 'casos') { const c = S.per === 'all' ? [1, 10, 50, 200] : [1, 3, 10, 40]; return { cort: c, cores: ['--q1', '--q2', '--q3', '--q4', '--q5'], rot: faixasRot(c, 0, true) }; }
    const c = cortesTaxa(S.tipo);
    return { cort: c, cores: ['--q1', '--q2', '--q3', '--q4', '--q5'].slice(5 - (c.length + 1)), rot: rotCurto(c) };
  }
  const classeDe = v => { let i = 0; while (i < CL.cort.length && v >= CL.cort[i]) i++; return i; };
  const corDe = v => css(CL.cores[classeDe(v)]);

  /* ---------- cartografia: centroides, símbolos proporcionais, hachura, contornos, rótulos ---------- */
  const R_MAX = 26;   // raio (px) do maior círculo; área do círculo ∝ casos, logo raio ∝ raiz quadrada dos casos
  const POLOS = ['João Pessoa', 'Campina Grande', 'Patos', 'Sousa', 'Cajazeiras', 'Guarabira', 'Monteiro'];   // em ordem de prioridade
  const TITULO_LEG = { taxa: 'Taxa por 100 mil mulheres por ano', casos: 'Casos notificados (número de notificações)', oe: 'Observado ÷ esperado (1 = igual ao estado; abaixo de 1, notifica menos)' };
  let grupoSimb, rSimb, camRegioes, camEstado, rotulos = [], centro = {}, ESC = null, estadoB, zoomInicial = 7.5, verRegioes = true, chavePadroes = '';
  let destacarPoucos = true, legAberta = innerWidth > 860;   // hachura ligada; legenda aberta no computador, recolhida no celular
  const raio = v => ESC.rmax * Math.sqrt(v / ESC.vmax);
  function areaAnel(a) { let s = 0; for (let i = 0; i < a.length - 1; i++) s += a[i][0] * a[i + 1][1] - a[i + 1][0] * a[i][1]; return s / 2; }
  function dentroAnel(pt, a) {
    let d = false;
    for (let i = 0, j = a.length - 1; i < a.length; j = i++) {
      const [xi, yi] = a[i], [xj, yj] = a[j];
      if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) d = !d;
    }
    return d;
  }
  // centroide do maior polígono do município; se cair fora (forma côncava), o ponto interno mais próximo dele
  function centroide(geom) {
    const polis = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
    let anel = polis[0][0], amax = -1;
    polis.forEach(pl => { const a = Math.abs(areaAnel(pl[0])); if (a > amax) { amax = a; anel = pl[0]; } });
    let cx = 0, cy = 0, A = 0;
    for (let i = 0; i < anel.length - 1; i++) { const [x0, y0] = anel[i], [x1, y1] = anel[i + 1], k = x0 * y1 - x1 * y0; A += k; cx += (x0 + x1) * k; cy += (y0 + y1) * k; }
    let c = [cx / (3 * A), cy / (3 * A)];
    if (!dentroAnel(c, anel)) {
      const xs = anel.map(p => p[0]), ys = anel.map(p => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
      let melhor = null;
      for (let i = 1; i < 20; i++) for (let j = 1; j < 20; j++) {
        const q = [x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * j / 20];
        if (dentroAnel(q, anel)) { const d = (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2; if (!melhor || d < melhor[1]) melhor = [q, d]; }
      }
      if (melhor) c = melhor[0];
    }
    return L.latLng(c[1], c[0]);
  }
  // hachura: linhas diagonais escuras sobre cores claras e claras sobre cores escuras (contraste ≥ 3:1)
  function luminancia(cor) {
    const h = cor.replace('#', ''), v = [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) / 255).map(c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  }
  // hachura do valor instável: linha fina (0,8 px a cada 10 px), cinza-escura com a MENOR opacidade que ainda dá contraste ≥ 3:1
  // com a cor; nas cores escuras, onde a linha escura não chega a 3:1, linha branca com a mesma regra
  const contrasteCor = (a, b) => { const x = luminancia(a), y = luminancia(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const hex = v => '#' + v.map(x => Math.round(x).toString(16).padStart(2, '0')).join('');
  const rgbDe = cor => [0, 2, 4].map(i => parseInt(cor.replace('#', '').substr(i, 2), 16));
  function linhaHachura(cor) {
    const f = rgbDe(cor);
    for (const base of [[38, 37, 34], [255, 255, 255]]) {
      for (let a = 0.3; a <= 1.0001; a += 0.05) {
        const mist = hex(base.map((b, i) => a * b + (1 - a) * f[i]));
        if (contrasteCor(mist, cor) >= 3) return { cor: hex(base), op: Math.round(a * 100) / 100 };
      }
    }
    return { cor: '#000000', op: 1 };
  }
  function padroes() {
    const cores = CL.cores.map(v => css(v)), chave = cores.join();
    if (chave === chavePadroes) return;
    chavePadroes = chave;
    const svg = map.getRenderer(camada.getLayers()[0])._container;
    let defs = svg.querySelector('defs');
    if (!defs) { defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs'); svg.insertBefore(defs, svg.firstChild); }
    defs.innerHTML = cores.map((cor, i) => { const l = linhaHachura(cor); return '<pattern id="hach-' + i + '" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">' +
      '<rect width="10" height="10" fill="' + cor + '"/><line x1="1" y1="0" x2="1" y2="10" stroke="' + l.cor + '" stroke-opacity="' + l.op + '" stroke-width="0.8"/></pattern>'; }).join('');
  }
  function desenharSimbolos() {
    grupoSimb.clearLayers(); ESC = null;
    if (S.ind !== 'casos') return;
    ESC = { vmax: Math.max(1, ...C.F.map(f => casosSel(f.properties))), rmax: R_MAX };   // escala do estado inteiro (comparável entre regiões)
    C.F.map(f => f.properties).filter(p => casosSel(p) > 0).sort((a, b) => casosSel(b) - casosSel(a)).forEach(p => {   // maiores primeiro = atrás
      const c = L.circleMarker(centro[p.cod], { renderer: rSimb, radius: raio(casosSel(p)), fillColor: css('--simbolo'), fillOpacity: 0.6, color: '#ffffff', weight: 0.8 });
      c.feature = { properties: p };
      ligar(c, p.cod, porCamada[p.cod]);
      c.addTo(grupoSimb);
      c.getElement().setAttribute('data-cod', p.cod);
    });
  }
  const estiloRegiao = f => (f.properties.cod === S.reg ? { fill: false, color: css('--accent'), weight: 3.2, opacity: 1 }
    : { fill: false, color: css('--limite-reg'), weight: 1.8, opacity: verRegioes ? 0.9 : 0 });
  // rótulos das cidades-polo: em ordem de prioridade, sem sobrepor outro rótulo, a ficha, a legenda ou o título
  function arrumarRotulos() {
    const vistos = [], evitar = ['painel', 'leg', 'mapatitulo'].map(id => $(id)).filter(e => e && e.offsetParent && e.style.display !== 'none').map(e => e.getBoundingClientRect());
    const caixa = $('map').getBoundingClientRect();   // o rótulo também não pode sair do mapa
    const bate = r => r.left < caixa.left + 2 || r.right > caixa.right - 2 || r.top < caixa.top + 2 || r.bottom > caixa.bottom - 2 ||
      [...vistos, ...evitar].some(o => !(r.right < o.left || r.left > o.right || r.bottom < o.top || r.top > o.bottom));
    rotulos.forEach((m, i) => {
      const el = m.getElement(); if (!el) return;
      el.style.visibility = 'visible';
      // tenta o texto à direita do ponto e, se bater em algo, à esquerda; senão, esconde
      const lado = ['', 'esq'].find(c => { el.classList.toggle('esq', c === 'esq'); return !bate(el.firstChild.getBoundingClientRect()); });
      if (lado === undefined || (i >= 5 && map.getZoom() < zoomInicial)) el.style.visibility = 'hidden'; else vistos.push(el.firstChild.getBoundingClientRect());
    });
  }
  // área livre do mapa: desconta o título e, com a ficha aberta, a largura (computador) ou a altura (celular) da ficha
  function areaLivre() {
    const big = innerWidth > 860, aberta = S.sel && !S.tabela && $('painel').style.display !== 'none';
    let br = [16, 16];
    if (aberta) br = big ? [$('painel').offsetWidth + 28, 16] : [16, $('painel').offsetHeight + 16];
    const esq = big && $('leg').offsetWidth ? $('leg').offsetWidth + 34 : 16;   // a legenda (canto inferior esquerdo) não cobre o estado
    return { paddingTopLeft: [esq, 56], paddingBottomRight: br };
  }
  const limitesRecorte = () => {
    if (!S.reg) return estadoB;
    const b = L.latLngBounds([]); C.F.filter(f => noRecorte(f.properties)).forEach(f => b.extend(porCamada[f.properties.cod].getBounds())); return b;
  };


  /* ---------- desenho ---------- */
  function estilizar() {
    CL = classes(); const bord = css('--limite-mun'), simb = S.ind === 'casos';
    $('mapwrap').classList.toggle('modo-casos', simb);
    if (!simb) padroes();
    camada.eachLayer(l => {
      const p = l.feature.properties, s = S.sel === p.cod, dentro = noRecorte(p), el = l.getElement(), instavel = !simb && destacarPoucos && casosSel(p) < MIN_CASOS;
      const fill = simb ? css('--base-mapa') : instavel ? 'url(#hach-' + classeDe(valor(p)) + ')' : corDe(valor(p));
      l.setStyle({ fillColor: fill, fillOpacity: dentro ? 1 : (simb ? 0.45 : 0.15), color: s ? css('--accent') : bord, weight: s ? 3.5 : 0.6 });
      el.tabIndex = dentro ? 0 : -1;
      el.setAttribute('data-instavel', instavel ? '1' : '0');
      el.setAttribute('aria-label', p.nome + ': ' + fmtValor(valor(p)) + (instavel ? ' (menos de 10 casos: valor instável)' : ''));
    });
    if (grupoSimb) grupoSimb.eachLayer(c => {
      const p = c.feature.properties, s = S.sel === p.cod, dentro = noRecorte(p);
      c.setStyle({ fillColor: css('--simbolo'), fillOpacity: dentro ? 0.6 : 0.12, opacity: dentro ? 1 : 0.25, color: s ? css('--accent') : '#ffffff', weight: s ? 2.5 : 0.8 });
    });
    if (camRegioes) camRegioes.setStyle(estiloRegiao);
    if (camEstado) camEstado.setStyle({ fill: false, color: css('--ink'), weight: 2.4, opacity: 0.9 });
    frente(S.sel);
  }
  // O selecionado vai para a frente (borda inteira visível); ao trocar, o anterior volta ao lugar em ordem alfabética
  function frente(cod) {
    if (naFrente && naFrente !== cod) {
      const el = porCamada[naFrente].getElement(), i = ORDEM.indexOf(naFrente), prox = ORDEM[i + 1] && porCamada[ORDEM[i + 1]].getElement();
      if (prox) el.parentNode.insertBefore(el, prox);
      naFrente = null;
    }
    if (cod && naFrente !== cod) { porCamada[cod].bringToFront(); naFrente = cod; }
  }
  /* ---------- dica (nome + valor): mouse segue o cursor; toque e teclado ficam acima do município, sem cobri-lo ---------- */
  function destacar(l, cor) { if (S.sel !== l.feature.properties.cod) l.setStyle({ weight: cor ? 3 : 2.5, color: css(cor || '--ink') }); }
  function dicaPerto(l, aviso, modo) {
    dicaModo = modo;
    const p = l.feature.properties, r = l.getElement().getBoundingClientRect(), m = $('map').getBoundingClientRect();
    tip.innerHTML = esc(p.nome + ' · ' + fmtValor(valor(p))) + '<small>' + aviso + '</small>';
    tip.style.display = 'block';
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let y = r.top - h - 6;
    if (y < m.top + 4) y = r.bottom + 6;
    tip.style.left = Math.max(4, Math.min(innerWidth - w - 4, r.left + r.width / 2 - w / 2)) + 'px';
    tip.style.top = y + 'px';
  }
  function esconderDica() { tip.style.display = 'none'; dicaCod = null; dicaModo = null; }
  // enquadra o recorte na área livre e só depois ajusta o limite de arraste (vista atual + meia Paraíba de margem),
  // para o limite nunca puxar o mapa de volta para trás da ficha
  function limitarArraste() { map.setMaxBounds(map.getBounds().extend(estadoB.pad(0.5))); }
  function enquadrar(b) { map.setMaxBounds(null); map.fitBounds(b || limitesRecorte(), Object.assign(areaLivre(), { animate: false })); limitarArraste(); }
  function legendaCirculos() {
    if (!ESC) return '';
    const ref = [1, 10, 100, 1000, 10000].filter(v => v <= ESC.vmax).slice(-3), rmax = raio(ref[ref.length - 1]), base = 2 * rmax + 6;
    let corpo = '', yAnt = -99;
    ref.slice().reverse().forEach(v => {   // do maior para o menor; rótulos a pelo menos 14 px um do outro
      const r = raio(v), topo = base - 2 * r, y = Math.max(topo + 4, yAnt + 14); yAnt = y;
      corpo += '<circle cx="' + (rmax + 2) + '" cy="' + (base - r) + '" r="' + r + '" fill="' + css('--simbolo') + '" fill-opacity=".35" stroke="' + css('--ink-2') + '" stroke-width="1"/>' +
        '<polyline points="' + (rmax + 2) + ',' + topo + ' ' + (2 * rmax + 10) + ',' + (y - 4) + '" fill="none" stroke="' + css('--ink-3') + '" stroke-dasharray="2 2"/>' +
        '<text x="' + (2 * rmax + 14) + '" y="' + y + '">' + nf(v) + (v === 1 ? ' caso' : ' casos') + '</text>';
    });
    const H = Math.ceil(Math.max(base + 2, yAnt + 4)), W = Math.ceil(2 * rmax + 90);
    return '<svg class="circ" width="' + W + '" height="' + H + '" role="img" aria-label="Círculos de referência: ' + ref.map(v => nf(v) + (v === 1 ? ' caso' : ' casos')).join(', ') + '">' + corpo + '</svg>';
  }
  function legenda() {
    let h = '<button type="button" class="leg-tog" aria-expanded="' + legAberta + '" aria-controls="legCorpo">Legenda</button><div class="leg-corpo" id="legCorpo">' +
      '<span class="leg-titulo">' + TITULO_LEG[S.ind] + '</span><div class="lsub">' + C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + ' · ' + (S.reg ? esc(nomeReg(S.reg)) : 'Paraíba') + '</div>';
    const ps = C.F.map(f => f.properties).filter(noRecorte);
    if (S.ind === 'casos') {
      const soma = ps.reduce((s, p) => s + casosSel(p), 0), sem = ps.filter(p => !casosSel(p)).length;
      h += legendaCirculos() + '<small>Área do círculo proporcional ao número de casos. ' + (S.reg ? 'Região' : 'Estado') + ': ' + nf(soma) + ' casos; ' + nf(sem) + (sem === 1 ? ' município' : ' municípios') + ' sem caso.</small>';
    } else {
      const n = CL.cores.map(() => 0); ps.forEach(p => n[classeDe(valor(p))]++);
      const nmax = Math.max(1, ...n), ref = S.ind === 'taxa' ? C.taxaEstado(S.tipo, S.per) : 1, iRef = classeDe(ref);
      CL.rot.forEach((r, i) => {
        h += '<div class="row" data-n="' + n[i] + '"><span class="sw" style="background:' + css(CL.cores[i]) + '"></span><span class="rot">' + r + (i === iRef ? ' <span class="media">◆</span>' : '') + '</span>' +
          (CL.fixas ? '<span class="hist" style="width:' + Math.round(26 * n[i] / nmax) + 'px"></span>' : '') + '<span class="cont">' + nf(n[i]) + '</span></div>';
      });
      const nInst = ps.filter(p => casosSel(p) < MIN_CASOS).length;
      if (destacarPoucos) h += '<div class="row inst"><span class="sw hach"></span><span class="rot">Menos de 10 casos: valor instável</span><span class="cont">' + nf(nInst) + '</span></div>';
      h += '<small>◆ ' + (S.ind === 'taxa' ? 'Média do estado: ' + nf(ref, 1) + '.' + (S.reg ? ' Média da ' + esc(nomeReg(S.reg)) + ': ' + nf(C.taxaRegiao(S.reg, S.tipo, S.per), 1) + '.' : '') : 'Classe do estado (1).') +
        ' Números: municípios em cada classe' + (S.reg ? ', na região' : '') + '.</small>';
      h += '<small>' + (S.ind === 'taxa' ? 'Classes fixas: quintis das taxas anuais dos municípios de 2019 a 2024 neste tipo, arredondados. Valem para qualquer ano ou período.' : 'Classes fixas em torno de 1 (igual ao estado).') + '</small>';
    }
    $('leg').innerHTML = h + '</div>';
    $('leg').classList.toggle('aberta', legAberta);
  }
  function ranking() {
    const todos = C.F.map(f => f.properties).filter(noRecorte);
    let lst, nota;
    if (S.rk === 'maiores') {
      lst = todos.sort((a, b) => valor(b) - valor(a)).slice(0, 10);
      nota = '* Menos de 10 casos no período: valor instável.';
    } else {
      lst = todos.filter(p => casosSel(p) >= MIN_CASOS).sort((a, b) => valor(a) - valor(b)).slice(0, 10);
      nota = 'Inclui só municípios com pelo menos 10 casos no tipo e período.';
    }
    $('rk').innerHTML = lst.map(p => '<li><a href="#mapa-' + p.cod + '" tabindex="0">' + esc(p.nome) + '</a>: ' + fmtValor(valor(p)) + (casosSel(p) < MIN_CASOS ? ' *' : '') + '</li>').join('') || '<li>Nenhum município com 10 casos ou mais neste filtro.</li>';
    $('rknota').textContent = (S.reg ? 'Só municípios da ' + nomeReg(S.reg) + '. ' : '') + nota;
    document.querySelectorAll('.rktabs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.r === S.rk)));
    $('rk').setAttribute('aria-label', S.rk === 'maiores' ? '10 maiores valores' : '10 menores valores, só municípios com pelo menos 10 casos');
  }
  function tabelaMapa() {
    if (!S.tabela) return;
    const linhas = C.F.map(f => f.properties).filter(noRecorte).sort((a, b) => valor(b) - valor(a));
    const at = k => (S.ind === k ? ' class="ativo"' : '');
    $('maptab').innerHTML = '<table><caption class="sr">' + esc(filtrosTexto()) + '</caption><thead><tr><th>Município</th><th>Mulheres</th><th' + at('casos') + '>Casos</th><th' + at('taxa') +
      '>Taxa por 100 mil/ano</th><th' + at('oe') + '>Observado ÷ esperado</th></tr></thead><tbody>' +
      linhas.map(p => '<tr data-c="' + p.cod + '" tabindex="0"><td>' + esc(p.nome) + (casosSel(p) < MIN_CASOS ? ' *' : '') + '</td><td>' + nf(p.pop) + '</td><td' + at('casos') + '>' + nf(casosSel(p)) + '</td><td' + at('taxa') + '>' +
        nf(C.taxa(p, S.tipo, S.per), 1) + '</td><td' + at('oe') + '>' + nf(C.oe(p, S.tipo, S.per), 2) + '</td></tr>').join('') +
      '</tbody></table><p class="hint" style="margin-top:8px">' + (S.reg ? nf(linhas.length) + ' municípios da ' + esc(nomeReg(S.reg)) + '. ' : '') + 'Mesmos valores e filtros do mapa, em ordem do indicador escolhido. * Menos de 10 casos no período: valor instável.</p>';
  }
  function atualizar() {
    $('indhint').textContent = HINT[S.ind];
    $('mapatitulo').textContent = filtrosTexto();
    desenharSimbolos(); estilizar(); legenda(); ranking(); tabelaMapa();
    if (S.sel) ficha();
  }

  /* ---------- ficha do município ---------- */
  function barras(pares, ref) {   // pares: [rótulo, valor]; ref: proporções do estado (marca preta)
    const mx = Math.max(1, ...pares.map(x => x[1])), tot = pares.reduce((s, x) => s + x[1], 0);
    const escala = ref ? Math.max(...pares.map(x => (tot ? x[1] / tot : 0)), ...ref) : 0;
    return '<div class="barras">' + pares.map(([r, v], i) => {
      const larg = ref ? (tot ? 100 * (v / tot) / escala : 0) : 100 * v / mx;
      const mark = ref ? '<span class="ref" style="left:' + (100 * ref[i] / escala) + '%" title="Estado: ' + nf(100 * ref[i], 0) + '%"></span>' : '';
      return '<span class="r">' + r + '</span><span class="tr"><span class="b" style="width:' + larg + '%"></span>' + mark + '</span><span class="n">' + nf(v) +
        (ref && tot ? ' <small>(' + nf(100 * v / tot, 0) + '%)</small>' : '') + '</span>';
    }).join('') + '</div>' + (ref ? '<div class="leg-ref">Barra: % do município. Traço: % do estado.</div>' : '');
  }
  // Frase com a faixa etária mais atingida (empates aparecem juntos; a faixa "Ignorada" não entra)
  function faixaTopo(p) {
    const tot = p.faixa.reduce((a, b) => a + b, 0), conhecidas = p.faixa.slice(0, 10), mx = Math.max(...conhecidas);
    if (!tot || !mx) return '<p class="fxtop">Nenhum caso com idade informada.</p>';
    const nomes = C.FX.slice(0, 10).map((f, i) => [f, conhecidas[i]]).filter(x => x[1] === mx).map(x => x[0] === '<1 Ano' ? 'menos de 1 ano' : C.rotFx(x[0]) + ' anos');
    return '<p class="fxtop">Faixa mais atingida: <b>' + nomes.join(' e ') + '</b> (' + nf(mx) + (nomes.length > 1 ? ' casos cada, ' : ' casos, ') + nf(100 * mx / tot, 0) + '%' + (nomes.length > 1 ? ' cada' : '') + ').</p>';
  }
  // Taxa por faixa: barra = município, traço preto = estado na mesma faixa; * = menos de 10 casos na faixa
  function barrasTaxa(p) {
    const tx = C.FX.map((_, i) => C.taxaFaixa(p, i)), te = C.FX.map((_, i) => C.taxaFaixaEstado(i));
    const escala = Math.max(1, ...tx.filter(v => v != null), ...te.filter(v => v != null));
    return '<div class="barras">' + C.FX.map((f, i) => {
      if (tx[i] == null) return '<span class="r">' + C.rotFx(f) + '</span><span class="tr semtaxa"></span><span class="n"><small>sem taxa (' + nf(p.faixa[i]) + (p.faixa[i] === 1 ? ' caso' : ' casos') + ')</small></span>';
      return '<span class="r">' + C.rotFx(f) + '</span><span class="tr"><span class="b" style="width:' + (100 * tx[i] / escala) + '%"></span>' +
        '<span class="ref" style="left:' + (100 * te[i] / escala) + '%" title="Estado: ' + nf(te[i], 1) + '"></span></span><span class="n">' + nf(tx[i], 1) + (p.faixa[i] < MIN_CASOS ? ' *' : '') + '</span>';
    }).join('') + '</div><div class="leg-ref">Barra: taxa do município. Traço: taxa do estado na mesma faixa (por 100 mil mulheres da faixa, por ano). ' +
      (p.faixa.slice(0, C.N_FX_TAXA).some(v => v < MIN_CASOS) ? '* Menos de 10 casos na faixa: valor instável. ' : '') + 'A faixa "Ignorada" não tem taxa.</div>';
  }
  const fxCorpo = p => (S.fx === 'taxa' ? barrasTaxa(p)
    : barras(C.FX.map((f, i) => [C.rotFx(f), p.faixa[i]]), p.faixa.some(v => v) ? C.faixaEstado.map(v => v / C.casosEstado('total', 'all')) : null));
  const alternaFx = () => '<div class="alterna noprint" role="group" aria-label="Mostrar a faixa etária como">' +
    [['casos', 'Casos'], ['taxa', 'Taxa por 100 mil/ano']].map(([k, t]) => '<button type="button" data-fx="' + k + '" aria-pressed="' + (S.fx === k) + '">' + t + '</button>').join('') + '</div>';
  // Serviços declarados pela prefeitura na MUNIC 2023: ícone + texto (nunca só cor); "-" da MUNIC = "Sem dado"
  const REDE = [['organismo_politicas_mulheres', 'Organismo de políticas para mulheres'], ['centro_referencia', 'Centro de referência ou atendimento especializado à mulher (CEAM/NIAM)'],
    ['casa_abrigo', 'Casa-abrigo ou acolhimento para mulheres em situação de violência'], ['delegacia_mulher', 'Delegacia especializada no atendimento à mulher']];
  const LEITURA_REDE = { 'Sim': ['sim', '✓', 'Sim'], 'Não': ['nao', '✕', 'Não'] };
  function htmlRede(p) {
    return '<div class="rede"><ul>' + REDE.map(([k, nome]) => {
      const v = p.rede[k], [cls, ic, txt] = LEITURA_REDE[v] || ['sd', '?', 'Sem dado'];
      return '<li class="' + cls + '" data-k="' + k + '" data-v="' + esc(v) + '"><span class="ic" aria-hidden="true">' + ic + '</span><span><b>' + txt + '</b> · ' + nome + '</span></li>';
    }).join('') + '</ul><p class="nota">Informação declarada pela prefeitura em 2023; serviços criados depois não aparecem.</p></div>';
  }
  // Onde as mulheres deste município foram atendidas (local da notificação): só contexto
  const NOTA_LOCAL = 'Atendimento em outra região pode indicar falta de serviço local ou referência regional; o dado não diz o motivo.';
  const CORES_LOCAL = ['--accent', '--barra', '--barra-claro'];
  function htmlLocal(p) {
    const tot = p.local[0] + p.local[1] + p.local[2];
    const rot = [C.LOCAIS[0] + (C.REG[p.reg] ? ' (' + esc(nomeReg(p.reg)) + ')' : ''), C.LOCAIS[1], C.LOCAIS[2]];
    return '<div class="local"><p class="nota" style="margin:0 0 6px">Todos os tipos. Local da notificação em relação à região de saúde de residência.</p>' +
      WS.util.barra100(rot.map((r, k) => ({ rot: r, n: p.local[k], cor: css(CORES_LOCAL[k]), k: k + 1 }))) +
      (tot && tot < MIN_CASOS ? '<div class="flag">Poucos casos (' + nf(tot) + '): porcentagens instáveis.</div>' : '') +
      '<p class="nota">' + NOTA_LOCAL + '</p></div>';
  }
  // O que olhar primeiro: frase-resumo calculada (mesmos cortes da legenda: 0,5 · 0,8 · 1,25 · 2)
  function resumoFicha(c, o, t, per) {
    const filtro = ' (' + C.TIPOS[t].toLowerCase() + ', ' + C.nomePer(per) + ')';
    if (!c) return { nivel: 'sd', txt: '<b>Nenhuma notificação</b>' + filtro + '.' };
    const n = o < 0.5 ? ['bem-menos', 'Notifica bem menos que o estado'] : o < 0.8 ? ['menos', 'Notifica menos que o estado'] : o <= 1.25 ? ['perto', 'Notifica perto da média do estado']
      : o <= 2 ? ['mais', 'Notifica mais que o estado'] : ['bem-mais', 'Notifica bem mais que o estado'];
    return { nivel: n[0], txt: '<b>' + n[1] + ':</b> ' + nf(o, 2) + ' do esperado' + filtro + '.' };
  }
  // seções recolhíveis (no celular, só os 5 indicadores começam abertos)
  const secao = (id, titulo, corpo) => '<details class="sec" data-sec="' + id + '"' + (id === 'ind' || innerWidth > 860 ? ' open' : '') + '><summary><h3>' + titulo + '</h3></summary>' + corpo + '</details>';
  function htmlFicha(p) {
    const t = S.tipo, per = S.per, c = C.casos(p, t, per), ce = C.casosEstado(t, per), tx = C.taxa(p, t, per), te = C.taxaEstado(t, per);
    const e = C.esperado(p, t, per), o = c / e, totEst = C.casosEstado('total', per);
    const tiposP = ['fisica', 'psicologica', 'sexual'].map(k => [C.TIPOS[k], C.casos(p, k, per)]);
    const totP = C.casos(p, 'total', per);
    const refTipos = ['fisica', 'psicologica', 'sexual'].map(k => C.casosEstado(k, per) / totEst);
    let h = '<button class="x noprint" type="button" aria-label="Fechar ficha">×</button><h2>' + esc(p.nome) + '</h2>' +
      '<div class="sub">' + nf(p.pop) + ' mulheres (Censo 2022) · ' + C.TIPOS[t] + ' · ' + C.nomePer(per) +
      (C.REG[p.reg] ? '<br>' + esc(nomeReg(p.reg)) + ' · ' + esc(C.REG[p.reg].macro) : '') + '</div>';
    const rs = resumoFicha(c, o, t, per);
    h += '<p class="resumo" data-nivel="' + rs.nivel + '">' + rs.txt + '</p>';
    if (c < MIN_CASOS) h += '<div class="flag">Poucos casos (' + nf(c) + ' no tipo e período): taxa e observado ÷ esperado instáveis.</div>';
    h += secao('ind', 'Os 5 indicadores', '<div class="ind5">' +
      '<div class="it"><div class="cab"><span>Casos notificados</span>' + linkCalc('casos') + '</div><div class="v">' + nf(c) + '</div><div class="c">Estado: ' + nf(ce) + ' (' + nf(100 * c / ce, 1) + '% do estado; ' + nf(100 * p.pop / C.POP, 1) + '% das mulheres)</div></div>' +
      '<div class="it"><div class="cab"><span>Taxa por 100 mil mulheres por ano</span>' + linkCalc('taxa') + '</div><div class="v">' + nf(tx, 1) + '</div><div class="c">Média do estado: ' + nf(te, 1) +
        (C.REG[p.reg] ? '<br>Média da região de saúde (' + esc(nomeReg(p.reg)) + '): ' + nf(C.taxaRegiao(p.reg, t, per), 1) : '') + '</div></div>' +
      '<div class="it"><div class="cab"><span>Observado ÷ esperado</span>' + linkCalc('oe') + '</div><div class="v">' + nf(o, 2) + '</div><div class="c">Esperado se seguisse o estado: ' + nf(e, 1) + ' casos · ' + C.leituraOE(o) + ' (estado = 1)</div></div>' +
      '<div class="it"><div class="cab"><span>Tipos de violência (' + C.nomePer(per) + ')</span>' + linkCalc('tipos') + '</div>' + barras(tiposP, totP ? refTipos : null) +
      '<div class="c">Total de notificações: ' + nf(totP) + '. Uma notificação pode ter mais de um tipo.</div></div>' +
      '<div class="it"><div class="cab"><span>Faixa etária (2019 a 2024, todos os tipos)</span>' + linkCalc('faixa') + '</div>' + faixaTopo(p) + '<div class="c">Detalhe por faixa abaixo, em casos ou em taxa.</div></div>' +
      '</div>');
    h += secao('faixa', 'Faixa etária em detalhe (2019 a 2024)', alternaFx() + '<div class="fxcorpo">' + fxCorpo(p) + '</div>');
    h += secao('ano', 'Casos por ano (' + C.TIPOS[t] + ')', barras(C.ANOS.map((a, i) => [String(a), p.casos[t][i]])));
    h += secao('local', 'Onde as mulheres deste município foram atendidas (2019 a 2024)', htmlLocal(p));
    h += secao('rede', 'Serviços declarados pelo município (MUNIC 2023, IBGE)', htmlRede(p));
    h += '<div class="btnrow noprint"><button class="btn peq pri" type="button" data-acao="imprimir">Imprimir ficha</button>' +
      '<button class="btn peq" type="button" data-acao="link">Copiar link da ficha</button><button class="btn peq" type="button" data-acao="comparar">Comparar municípios</button></div>';
    return h;
  }
  function ficha() {
    const p = C.porCod[S.sel], el = $('painel');
    el.innerHTML = htmlFicha(p); el.style.display = 'block';
    $('mapwrap').classList.add('com-ficha');   // no celular, esconde legenda, escala e fonte enquanto a ficha está aberta
    el.querySelector('.x').addEventListener('click', () => { location.hash = '#mapa'; });
    el.querySelector('[data-acao=imprimir]').addEventListener('click', imprimirFicha);
    el.querySelector('[data-acao=link]').addEventListener('click', () => WS.util.copiar(location.href.split('#')[0] + '#mapa-' + p.cod, 'Link da ficha copiado'));
    el.querySelector('[data-acao=comparar]').addEventListener('click', () => abrirComparar([p.cod]));
    el.querySelectorAll('[data-fx]').forEach(b => b.addEventListener('click', () => {
      S.fx = b.dataset.fx; el.querySelector('.fxcorpo').innerHTML = fxCorpo(p);
      el.querySelectorAll('[data-fx]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.fx === S.fx)));
    }));
  }
  let voltarFoco = null;
  function mostrarFicha(cod, { focar = false } = {}) {
    if (!C.porCod[cod]) return false;
    if (!S.sel && document.activeElement && document.activeElement !== document.body && !$('painel').contains(document.activeElement)) voltarFoco = document.activeElement;
    S.sel = cod;
    if (S.tabela) alternarTabela(false);
    estilizar(); ficha(); enquadrar();
    if (focar) $('painel').querySelector('h2').setAttribute('tabindex', '-1'), $('painel').querySelector('h2').focus();
    return true;
  }
  function fecharFicha() {
    const estavaNaFicha = $('painel').contains(document.activeElement);
    S.sel = null; $('painel').style.display = 'none'; $('painel').innerHTML = ''; $('mapwrap').classList.remove('com-ficha'); estilizar();
    if (estavaNaFicha || voltarFoco) { const alvo = voltarFoco && document.contains(voltarFoco) && voltarFoco.getClientRects().length ? voltarFoco : $('mapatitulo'); alvo.focus({ preventScroll: true }); }
    voltarFoco = null;
  }

  // Imprimir ficha: monta uma folha limpa em #impressao (só a ficha, com filtros, fonte e data)
  function imprimirFicha() {
    const p = C.porCod[S.sel], hoje = new Date().toLocaleDateString('pt-BR');
    $('impressao').innerHTML = '<div class="ficha"><div style="font-size:10pt;color:#444">Violência contra a mulher na Paraíba · ficha do município</div>' + htmlFicha(p) +
      '<div class="rodape">Fonte: SINAN/TABNET (notificações de mulheres, município de residência, sem violência autoprovocada) e Censo 2022 (IBGE). ' +
      'Os números mostram casos notificados, não todos os que acontecem. Impresso em ' + hoje + '. Endereço: ' + esc(location.href.split('#')[0] + '#mapa-' + p.cod) + '</div></div>';
    $('impressao').querySelectorAll('details').forEach(d => { d.open = true; });
    document.body.classList.add('imprimindo');
    const limpar = () => { document.body.classList.remove('imprimindo'); window.removeEventListener('afterprint', limpar); };
    window.addEventListener('afterprint', limpar);
    window.print();
  }

  /* ---------- tabela do mapa ---------- */
  function alternarTabela(on) {
    S.tabela = on == null ? !S.tabela : on;
    $('maptab').classList.toggle('on', S.tabela);
    $('verTabela').textContent = S.tabela ? 'Ver mapa' : 'Ver como tabela';
    $('verTabela').setAttribute('aria-pressed', String(S.tabela));
    if (S.tabela) { $('painel').style.display = 'none'; tabelaMapa(); } else { if (S.sel) ficha(); setTimeout(() => map.invalidateSize(), 30); }
  }

  /* ---------- comparar municípios ---------- */
  const acharCod = txt => { const q = semAc(txt || ''); if (!q) return null; const f = C.F.find(f => semAc(f.properties.nome) === q) || C.F.find(f => semAc(f.properties.nome).startsWith(q)); return f ? f.properties.cod : null; };
  const GRUPOS_FX = [['Até 9 anos', [0, 1, 2]], ['10 a 19 anos', [3, 4]], ['20 a 29 anos', [5]], ['30 a 39 anos', [6]], ['40 a 59 anos', [7, 8]], ['60 anos ou mais', [9]], ['Ignorada', [10]]];
  function abrirComparar(cods) {
    const ins = ['cmp1', 'cmp2', 'cmp3'].map(id => $(id));
    (cods || []).forEach((c, i) => { if (ins[i] && C.porCod[c]) ins[i].value = C.porCod[c].nome; });
    $('cmpSub').textContent = 'Escolha 2 ou 3 municípios. Tipo e período seguem os filtros do mapa: ' + C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + '. A última coluna é a média do estado.';
    if (!$('cmp').open) $('cmp').showModal();
    compararRender();
    const vazio = ins.find(i => !i.value); (vazio || ins[0]).focus();
  }
  function compararRender() {
    const cods = ['cmp1', 'cmp2', 'cmp3'].map(id => acharCod($(id).value)).filter((c, i, a) => c && a.indexOf(c) === i);
    if (cods.length < 2) { $('cmpRes').innerHTML = '<p class="hint" style="margin:8px 0 0">Escolha pelo menos 2 municípios.</p>'; return; }
    const ps = cods.map(c => C.porCod[c]), t = S.tipo, per = S.per, totEst = C.casosEstado('total', per), totFxEst = C.casosEstado('total', 'all');
    const linha = (rot, vals, est, cls) => '<tr' + (cls ? ' class="' + cls + '"' : '') + '><td>' + rot + '</td>' + vals.map(v => '<td>' + v + '</td>').join('') + '<td class="ref">' + est + '</td></tr>';
    const pct = (a, b) => (b ? nf(100 * a / b, 1) + '%' : '–');
    let h = '<table data-tipo="' + t + '" data-per="' + per + '"><thead><tr><th>Indicador</th>' + ps.map(p => '<th data-c="' + p.cod + '">' + esc(p.nome) + (C.casos(p, t, per) < MIN_CASOS ? ' *' : '') + '</th>').join('') + '<th class="ref">Estado (referência)</th></tr></thead><tbody>';
    h += linha('Mulheres (Censo 2022)', ps.map(p => nf(p.pop)), nf(C.POP));
    h += linha('Casos notificados', ps.map(p => nf(C.casos(p, t, per))), nf(C.casosEstado(t, per)));
    h += linha('Taxa por 100 mil mulheres por ano', ps.map(p => nf(C.taxa(p, t, per), 1)), nf(C.taxaEstado(t, per), 1));
    h += linha('Casos esperados se seguisse o estado', ps.map(p => nf(C.esperado(p, t, per), 1)), nf(C.casosEstado(t, per)));
    h += linha('Observado ÷ esperado', ps.map(p => nf(C.oe(p, t, per), 2)), '1,00');
    h += '<tr class="grupo"><td colspan="' + (ps.length + 2) + '">Tipos de violência (% das notificações, ' + C.nomePer(per) + ')</td></tr>';
    ['fisica', 'psicologica', 'sexual'].forEach(k => { h += linha(C.TIPOS[k], ps.map(p => pct(C.casos(p, k, per), C.casos(p, 'total', per))), pct(C.casosEstado(k, per), totEst)); });
    h += '<tr class="grupo"><td colspan="' + (ps.length + 2) + '">Faixa etária (% das notificações, 2019 a 2024, todos os tipos)</td></tr>';
    GRUPOS_FX.forEach(([rot, idx]) => {
      const somaP = p => idx.reduce((s, i) => s + p.faixa[i], 0), totP = p => p.faixa.reduce((a, b) => a + b, 0);
      h += linha(rot, ps.map(p => pct(somaP(p), totP(p))), pct(idx.reduce((s, i) => s + C.faixaEstado[i], 0), totFxEst));
    });
    h += '</tbody></table><p class="hint" style="margin-top:8px">* menos de 10 casos no período: valores instáveis. Tipos somam mais de 100% porque uma notificação pode ter mais de um tipo.</p>';
    $('cmpRes').innerHTML = h;
  }

  // mesmos eventos para o polígono e para o círculo do município (destaque sempre no polígono)
  function ligar(l, cod, poli) {
    l.on('mousemove', e => {
      if (ponteiro === 'touch') return;
      const p = poli.feature.properties;
      tip.style.display = 'block'; tip.textContent = p.nome + ' · ' + fmtValor(valor(p));
      tip.style.left = (e.originalEvent.clientX + 14) + 'px'; tip.style.top = (e.originalEvent.clientY - 34) + 'px';
      destacar(poli);
    });
    l.on('mouseout', () => { if (ponteiro !== 'touch') { esconderDica(); estilizar(); } });
    // toque: o 1º toque mostra a etiqueta acima do município; o 2º no mesmo município abre a ficha
    l.on('click', e => {
      L.DomEvent.stopPropagation(e);
      if (ponteiro === 'touch' && dicaCod !== cod) { estilizar(); destacar(poli); dicaPerto(poli, 'Toque de novo para abrir a ficha', 'toque'); dicaCod = cod; return; }
      esconderDica(); location.hash = '#mapa-' + cod;
    });
  }

  /* ---------- Baixar mapa (PNG): redesenha o mapa atual num canvas, com título, legenda e fonte ---------- */
  function caminho(g, geom) {
    const polis = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
    g.beginPath();
    polis.forEach(pl => pl.forEach(anel => anel.forEach((c, i) => { const pt = map.latLngToContainerPoint([c[1], c[0]]); if (i) g.lineTo(pt.x, pt.y); else g.moveTo(pt.x, pt.y); })));
  }
  function padraoCanvas(g, cor) {
    const t = document.createElement('canvas'); t.width = t.height = 8;
    const k = t.getContext('2d'); k.fillStyle = cor; k.fillRect(0, 0, 8, 8);
    const l = linhaHachura(cor); k.strokeStyle = l.cor; k.globalAlpha = l.op; k.lineWidth = 0.8;
    [[0, 8, 8, 0], [-4, 4, 4, -4], [4, 12, 12, 4]].forEach(([a, b, c, d]) => { k.beginPath(); k.moveTo(a, b); k.lineTo(c, d); k.stroke(); });
    return g.createPattern(t, 'repeat');
  }
  function quebrar(g, txt, x, y, larg, alt) {
    let linha = '';
    txt.split(' ').forEach(p => { const t = linha ? linha + ' ' + p : p; if (g.measureText(t).width > larg && linha) { g.fillText(linha, x, y); y += alt; linha = p; } else linha = t; });
    if (linha) g.fillText(linha, x, y);
    return y + alt;
  }
  async function baixarPNG() {
    try {
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const sz = map.getSize(), LEG = 300, TOPO = 78, BASE = 50, E = 2, W = sz.x + LEG, H = TOPO + Math.max(sz.y, 420) + BASE;
      const cv = document.createElement('canvas'); cv.width = W * E; cv.height = H * E;
      const g = cv.getContext('2d'); g.scale(E, E);
      const sans = '"IBM Plex Sans", system-ui, sans-serif', serif = '"IBM Plex Serif", Georgia, serif';
      g.fillStyle = css('--bg'); g.fillRect(0, 0, W, H);
      g.fillStyle = css('--ink'); g.font = '600 21px ' + serif; g.fillText(TITULO_LEG[S.ind], 20, 34);
      g.fillStyle = css('--ink-2'); g.font = '14px ' + sans; g.fillText(C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + ' · ' + (S.reg ? nomeReg(S.reg) : 'Paraíba'), 20, 58);
      // mapa
      g.save(); g.translate(0, TOPO); g.beginPath(); g.rect(0, 0, sz.x, sz.y); g.clip();
      g.fillStyle = css('--surface-2'); g.fillRect(0, 0, sz.x, sz.y);
      const pad = {};
      camada.eachLayer(l => {
        const o = l.options, m = /url\(#hach-(\d)\)/.exec(o.fillColor || '');
        caminho(g, l.feature.geometry);
        g.globalAlpha = o.fillOpacity; g.fillStyle = m ? (pad[m[1]] = pad[m[1]] || padraoCanvas(g, css(CL.cores[+m[1]]))) : o.fillColor; g.fill('evenodd');
        g.globalAlpha = 1; g.strokeStyle = o.color; g.lineWidth = o.weight; g.stroke();
      });
      [camRegioes, camEstado].forEach(cam => cam && cam.eachLayer(l => { const o = l.options; if (!o.opacity) return; caminho(g, l.feature.geometry); g.globalAlpha = o.opacity; g.strokeStyle = o.color; g.lineWidth = o.weight; g.stroke(); g.globalAlpha = 1; }));
      grupoSimb.eachLayer(c => {
        const pt = map.latLngToContainerPoint(c.getLatLng()), o = c.options;
        g.beginPath(); g.arc(pt.x, pt.y, c.getRadius(), 0, 2 * Math.PI);
        g.globalAlpha = o.fillOpacity; g.fillStyle = o.fillColor; g.fill(); g.globalAlpha = o.opacity; g.strokeStyle = o.color; g.lineWidth = o.weight; g.stroke(); g.globalAlpha = 1;
      });
      g.font = '600 12px ' + sans; g.lineJoin = 'round';
      rotulos.forEach(mk => {
        if (!mk.getElement() || mk.getElement().style.visibility === 'hidden') return;
        const pt = map.latLngToContainerPoint(mk.getLatLng()), nome = mk.options.title, esq = mk.getElement().classList.contains('esq'), tx = esq ? pt.x - 6 - g.measureText(nome).width : pt.x + 6;
        g.fillStyle = css('--ink'); if (S.ind !== 'casos') { g.beginPath(); g.arc(pt.x, pt.y, 2.5, 0, 2 * Math.PI); g.fill(); }
        g.strokeStyle = css('--bg'); g.lineWidth = 3; g.strokeText(nome, tx, pt.y - 4); g.fillText(nome, tx, pt.y - 4);
      });
      // barra de escala
      const y0 = sz.y / 2, m100 = map.distance(map.containerPointToLatLng([0, y0]), map.containerPointToLatLng([100, y0]));
      const km = [1, 2, 5, 10, 20, 50, 100, 200].filter(k => k * 1000 / m100 * 100 <= 140).pop() || 1, px = km * 1000 / m100 * 100;
      g.fillStyle = css('--ink-2'); g.fillRect(16, sz.y - 22, px, 2); g.fillRect(16, sz.y - 28, 1.5, 8); g.fillRect(16 + px - 1.5, sz.y - 28, 1.5, 8);
      g.font = '12px ' + sans; g.fillText(km + ' km', 20 + px, sz.y - 18);
      g.restore();
      // legenda
      let x = sz.x + 20, y = TOPO + 24;
      g.fillStyle = css('--ink'); g.font = '600 14px ' + sans; y = quebrar(g, TITULO_LEG[S.ind], x, y, LEG - 36, 18) + 4;
      g.font = '13px ' + sans;
      const ps = C.F.map(f => f.properties).filter(noRecorte);
      if (S.ind === 'casos' && ESC) {
        const ref = [1, 10, 100, 1000, 10000].filter(v => v <= ESC.vmax).slice(-3);
        ref.slice().reverse().forEach(v => {
          const r = raio(v); y += r + 4;
          g.beginPath(); g.arc(x + R_MAX, y, r, 0, 2 * Math.PI); g.globalAlpha = 0.4; g.fillStyle = css('--simbolo'); g.fill(); g.globalAlpha = 1;
          g.strokeStyle = css('--ink-2'); g.lineWidth = 1; g.stroke(); g.fillStyle = css('--ink'); g.fillText(nf(v) + (v === 1 ? ' caso' : ' casos'), x + 2 * R_MAX + 12, y + 4); y += r + 6;
        });
        g.fillStyle = css('--ink-2'); g.font = '12px ' + sans; y = quebrar(g, 'Área do círculo proporcional ao número de casos.', x, y + 12, LEG - 36, 16);
      } else {
        const n = CL.cores.map(() => 0); ps.forEach(p => n[classeDe(valor(p))]++);
        CL.rot.forEach((r, i) => { g.fillStyle = css(CL.cores[i]); g.fillRect(x, y - 10, 18, 12); g.fillStyle = css('--ink'); g.fillText(r + ' (' + nf(n[i]) + ')', x + 26, y); y += 20; });
        g.fillStyle = padraoCanvas(g, css('--q2')); g.fillRect(x, y - 10, 18, 12); g.fillStyle = css('--ink');
        g.fillText('Menos de 10 casos: valor instável (' + nf(ps.filter(p => casosSel(p) < MIN_CASOS).length) + ')', x + 26, y); y += 24;
        g.fillStyle = css('--ink-2'); g.font = '12px ' + sans;
        y = quebrar(g, (S.ind === 'taxa' ? 'Média do estado: ' + nf(C.taxaEstado(S.tipo, S.per), 1) + ' por 100 mil/ano. Classes por quintis.' : 'Classes fixas em torno de 1 (igual ao estado).') + ' Entre parênteses: municípios em cada classe.', x, y, LEG - 36, 16);
      }
      // fonte
      g.fillStyle = css('--ink-3'); g.font = '12px ' + sans;
      g.fillText('Fonte: SINAN/TABNET (Ministério da Saúde), notificações de 2019 a 2024; IBGE, Censo 2022 e malha municipal. Gerado em ' + new Date().toLocaleDateString('pt-BR') + ' · github.com/AnaCAmim/TCC', 20, H - 20);
      const nome = 'mapa_' + S.ind + '_' + S.tipo + '_' + (S.per === 'all' ? '2019-2024' : S.per) + (S.reg ? '_regiao' + S.reg : '') + '.png';
      await new Promise((ok, erro) => cv.toBlob(b => {
        if (!b) return erro(new Error('sem imagem'));
        const url = URL.createObjectURL(b), a = document.createElement('a'); a.href = url; a.download = nome;
        document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); ok();
      }, 'image/png'));
    } catch (e) {
      WS.util.toast('Não foi possível gerar a imagem neste modo de abertura. Abra o painel pelo link publicado.');
    }
  }

  // contornos (estado e regiões de saúde) e rótulos das cidades-polo: só referência; entram logo depois do primeiro desenho
  function referencias() {
    if (C.CONTORNOS) {
      camRegioes = L.geoJSON({ type: 'FeatureCollection', features: C.CONTORNOS.regioes.map(r => ({ type: 'Feature', properties: { cod: r.cod }, geometry: r.geom })) },
        { pane: 'regioes', renderer: L.svg({ pane: 'regioes' }), interactive: false, style: estiloRegiao }).addTo(map);
      camEstado = L.geoJSON({ type: 'Feature', properties: {}, geometry: C.CONTORNOS.estado }, { pane: 'estado', renderer: L.svg({ pane: 'estado' }), interactive: false,
        style: () => ({ fill: false, color: css('--ink'), weight: 2.4, opacity: 0.9 }) }).addTo(map);
    }
    rotulos = POLOS.map(n => C.F.find(f => f.properties.nome === n)).filter(Boolean).map(f => L.marker(centro[f.properties.cod], {
      pane: 'rotulos', interactive: false, keyboard: false, title: f.properties.nome,
      icon: L.divIcon({ className: 'rotulo', html: '<span>' + esc(f.properties.nome) + '</span>', iconSize: null, iconAnchor: [0, 0] }) }).addTo(map));
    rotulos.forEach(m => { const el = m.getElement(); el.setAttribute('aria-hidden', 'true'); el.removeAttribute('title'); el.removeAttribute('tabindex'); });
    estilizar(); arrumarRotulos();
  }

  /* ---------- início ---------- */
  function iniciar(calc) {
    C = calc;
    map = L.map('map', { zoomSnap: 0.25, attributionControl: false, keyboard: true, maxBoundsViscosity: 0.9 }).setView([-7.12, -36.8], 7.5);
    tip = $('tip');
    const alfabetica = [...C.F].sort((a, b) => a.properties.nome.localeCompare(b.properties.nome, 'pt'));
    ORDEM = alfabetica.map(f => f.properties.cod);
    camada = L.geoJSON({ type: 'FeatureCollection', features: alfabetica }, { style: () => ({}), onEachFeature: (f, l) => {
      porCamada[f.properties.cod] = l;
      centro[f.properties.cod] = centroide(f.geometry);
      ligar(l, f.properties.cod, l);
    } });
    // vista final calculada ANTES de pôr as camadas no mapa: cada geometria é projetada uma vez só (abertura mais leve)
    estadoB = camada.getBounds();
    CL = classes(); legenda();
    map.fitBounds(estadoB, Object.assign(areaLivre(), { animate: false }));
    zoomInicial = map.getZoom();
    map.setMinZoom(Math.max(4, zoomInicial - 1.5)); map.setMaxZoom(11);
    camada.addTo(map);
    // referências: regiões de saúde, contorno do estado, círculos, rótulos das cidades-polo
    [['regioes', 410], ['estado', 415], ['simbolos', 420], ['rotulos', 640]].forEach(([n, z]) => { const p = map.createPane(n); p.style.zIndex = z; if (n !== 'simbolos') p.style.pointerEvents = 'none'; });
    rSimb = L.svg({ pane: 'simbolos' }); grupoSimb = L.layerGroup().addTo(map);
    const Fonte = L.Control.extend({ options: { position: 'bottomleft' }, onAdd: () => { const d = L.DomUtil.create('div', 'fonte-mapa'); d.textContent = 'Fonte: SINAN/TABNET, 2019 a 2024; IBGE, Censo 2022 e malha municipal'; return d; } });
    new Fonte().addTo(map);
    L.control.scale({ position: 'bottomleft', imperial: false, maxWidth: 110 }).addTo(map);
    // legenda como controle do mapa, acima da escala e da fonte: fica visível também com a ficha aberta
    const Legenda = L.Control.extend({ options: { position: 'bottomleft' }, onAdd: () => { const d = $('leg'); L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d); return d; } });
    new Legenda().addTo(map);
    $('leg').addEventListener('click', e => { if (e.target.closest('.leg-tog')) { legAberta = !legAberta; legenda(); } });
    const Estado = L.Control.extend({ options: { position: 'topleft' }, onAdd: () => {
      const d = L.DomUtil.create('div', 'leaflet-bar ctl-estado'), b = L.DomUtil.create('button', '', d);
      b.type = 'button'; b.id = 'verEstado'; b.setAttribute('aria-label', 'Ver estado inteiro'); b.title = 'Ver estado inteiro'; b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/></svg>';
      L.DomEvent.disableClickPropagation(d); b.addEventListener('click', () => enquadrar(estadoB));
      return d; } });
    new Estado().addTo(map);
    // teclado: Tab percorre os municípios (ordem alfabética), a etiqueta aparece acima, Enter abre a ficha
    camada.eachLayer(l => {
      const el = l.getElement(), cod = l.feature.properties.cod;
      el.setAttribute('role', 'button');
      el.addEventListener('focus', () => {
        if (ponteiro !== 'teclado') return;      // foco vindo de clique ou toque: a dica é a do mouse/toque
        const b = l.getBounds();
        if (!map.getBounds().contains(b)) map.panTo(b.getCenter(), { animate: false });
        estilizar(); destacar(l, '--accent'); dicaPerto(l, 'Enter abre a ficha', 'teclado');
      });
      el.addEventListener('blur', () => { if (dicaModo === 'teclado') { esconderDica(); estilizar(); } });
      el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); esconderDica(); location.hash = '#mapa-' + cod; } });
    });
    $('map').addEventListener('pointerdown', e => { ponteiro = e.pointerType; }, true);
    document.addEventListener('keydown', () => { ponteiro = 'teclado'; }, true);
    $('map').addEventListener('scroll', e => { e.target.scrollTop = 0; e.target.scrollLeft = 0; });   // o foco num polígono não pode rolar o mapa
    map.on('click movestart zoomstart', () => { if (dicaCod) { esconderDica(); estilizar(); } });
    limitarArraste();   // o arraste não sai da Paraíba (com margem)
    map.on('zoomend moveend resize', arrumarRotulos);

    $('per').innerHTML = '<option value="all">2019 a 2024 (soma)</option>' + C.ANOS.map(a => '<option value="' + a + '">' + a + '</option>').join('');
    ['ind', 'tipo', 'per'].forEach(id => $(id).addEventListener('change', e => { S[id] = e.target.value; atualizar(); }));
    const porMacro = {};
    Object.entries(C.REG).forEach(([cod, r]) => (porMacro[r.macro] = porMacro[r.macro] || []).push(cod));
    $('reg').innerHTML = '<option value="">Todo o estado</option>' + Object.keys(porMacro).sort().map(m => '<optgroup label="' + esc(m) + '">' +
      porMacro[m].map(c => '<option value="' + c + '">' + esc(C.REG[c].nome) + ' (' + C.munsRegiao(c).length + ' municípios)</option>').join('') + '</optgroup>').join('');
    $('reg').addEventListener('change', e => { S.reg = e.target.value; atualizar(); enquadrar(); });
    $('verRegioes').addEventListener('change', e => { verRegioes = e.target.checked; estilizar(); });
    $('destacarPoucos').addEventListener('change', e => { destacarPoucos = e.target.checked; estilizar(); legenda(); });
    $('baixarPng').addEventListener('click', baixarPNG);
    $('lista').innerHTML = C.F.map(f => '<option value="' + esc(f.properties.nome) + '">').join('');
    const buscar = txt => {
      const c = acharCod(txt);
      $('buscaMsg').textContent = !txt.trim() || c ? '' : 'Nenhum município encontrado para "' + txt.trim() + '". Confira o nome (acentos e maiúsculas não importam).';
      if (c) location.hash = '#mapa-' + c;
    };
    $('busca').addEventListener('change', e => buscar(e.target.value));
    $('busca').addEventListener('keydown', e => { if (e.key === 'Enter') buscar(e.target.value); });
    document.querySelectorAll('.rktabs button').forEach(b => b.addEventListener('click', () => { S.rk = b.dataset.r; ranking(); }));
    $('verTabela').addEventListener('click', () => alternarTabela());
    $('maptab').addEventListener('click', e => { const tr = e.target.closest('tr[data-c]'); if (tr) location.hash = '#mapa-' + tr.dataset.c; });
    $('maptab').addEventListener('keydown', e => { const tr = e.target.closest('tr[data-c]'); if (tr && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); location.hash = '#mapa-' + tr.dataset.c; } });
    $('abrirComparar').addEventListener('click', () => abrirComparar(S.sel ? [S.sel] : []));
    ['cmp1', 'cmp2', 'cmp3'].forEach(id => $(id).addEventListener('input', compararRender));
    $('cmpFechar').addEventListener('click', () => $('cmp').close());
    // Esc sempre fecha a comparação, mesmo com o foco num campo preenchido
    $('cmp').addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); $('cmp').close(); } });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && tip.style.display === 'block') esconderDica(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !e.defaultPrevented && S.sel && !$('cmp').open && !e.target.closest('input,select')) { e.preventDefault(); location.hash = '#mapa'; } });
    atualizar();
    setTimeout(referencias, 0);   // divide o trabalho da abertura em duas tarefas curtas
    // usado pelo tour: muda um filtro como se a pessoa tivesse escolhido na lista
    const definir = (id, v) => { $(id).value = v; $(id).dispatchEvent(new Event('change')); };
    const verFaixaTaxa = () => { const b = $('painel').querySelector('[data-fx=taxa]'); if (!b) return; b.closest('details').open = true; b.click(); b.closest('details').scrollIntoView({ block: 'start' }); };
    return { S, mostrarFicha, fecharFicha, abrirComparar, imprimirFicha, alternarTabela, redesenhar: () => { estilizar(); legenda(); }, invalidar: () => map.invalidateSize(), definir, verFaixaTaxa,
      limitesMapa: () => map.getBounds(),
      // ganchos para o teste: escala dos símbolos, hachura e enquadramento
      simbolos: () => ({ escala: ESC, raios: Object.fromEntries(grupoSimb.getLayers().map(c => [c.feature.properties.cod, c.getRadius()])),
        ordem: grupoSimb.getLayers().map(c => c.feature.properties.cod) }),
      enquadramento: () => { const ne = map.latLngToContainerPoint(estadoB.getNorthEast()), sw = map.latLngToContainerPoint(estadoB.getSouthWest()), sz = map.getSize();
        return { x0: sw.x, x1: ne.x, y0: ne.y, y1: sw.y, w: sz.x, h: sz.y }; },
      baixarPNG };
  }
  return { iniciar };
})();
