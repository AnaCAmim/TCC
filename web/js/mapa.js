/* mapa.js: tela Mapa (filtros, mapa coroplético, título com filtros, legenda, ranking, tabela do mapa,
   ficha do município com impressão, comparação de municípios). Usa só as fórmulas de calculo.js. */
"use strict";
window.WS = window.WS || {};
WS.mapa = (function () {
  const { $, nf, css, esc, semAc } = WS.util;
  const S = { ind: 'taxa', tipo: 'total', per: 'all', reg: '', sel: null, rk: 'maiores', tabela: false };
  const MIN_CASOS = 10;   // abaixo disso a taxa e o observado ÷ esperado ficam instáveis
  const HINT = {
    taxa: 'Casos por ano para cada 100 mil mulheres. Permite comparar municípios de tamanhos diferentes.',
    casos: 'Quantidade de notificações. Mostra onde está o volume de atendimento.',
    oe: 'Compara o município com o estado: 1 é igual, abaixo de 1 notifica menos, acima notifica mais.'
  };
  let C, map, camada, CL, porCamada = {}, ORDEM = [], naFrente = null, tip, ponteiro = 'mouse', dicaCod = null, dicaModo = null;
  const noRecorte = p => !S.reg || p.reg === S.reg;          // município dentro da região de saúde escolhida
  const nomeReg = cod => (C.REG[cod] ? C.REG[cod].nome : '');

  const valor = p => C.valor(p, S.ind, S.tipo, S.per);
  const casosSel = p => C.casos(p, S.tipo, S.per);
  const fmtValor = v => (S.ind === 'casos' ? nf(v) + (v === 1 ? ' caso' : ' casos') : S.ind === 'taxa' ? nf(v, 1) + ' por 100 mil/ano' : nf(v, 2) + '× o esperado');
  const filtrosTexto = () => C.NOME_IND[S.ind].replace(' por ano', '') + ' · ' + C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + (S.reg ? ' · ' + nomeReg(S.reg) : '');
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
  function classes() {
    if (S.ind === 'oe') return { cort: [0.5, 0.8, 1.25, 2], cores: ['--d1', '--d2', '--d3', '--d4', '--d5'],
      rot: ['Menos da metade do esperado (abaixo de 0,5)', 'Abaixo do esperado (0,5 a 0,8)', 'Próximo da média do estado (0,8 a 1,25)', 'Acima do esperado (1,25 a 2)', 'Mais do dobro do esperado (2 ou mais)'] };
    if (S.ind === 'casos') { const c = S.per === 'all' ? [1, 10, 50, 200] : [1, 3, 10, 40]; return { cort: c, cores: ['--q1', '--q2', '--q3', '--q4', '--q5'], rot: faixasRot(c, 0, true) }; }
    let c = quantis(C.F.map(f => valor(f.properties)), 5).map(x => Math.round(x));
    c = c.filter((x, i) => i === 0 || x > c[i - 1]);
    return { cort: c, cores: ['--q1', '--q2', '--q3', '--q4', '--q5'].slice(5 - (c.length + 1)), rot: faixasRot(c, 0) };
  }
  const corDe = v => { let i = 0; while (i < CL.cort.length && v >= CL.cort[i]) i++; return css(CL.cores[i]); };

  /* ---------- desenho ---------- */
  function estilizar() {
    CL = classes(); const bord = css('--surface');
    camada.eachLayer(l => {
      const p = l.feature.properties, s = S.sel === p.cod, dentro = noRecorte(p), el = l.getElement();
      l.setStyle({ fillColor: corDe(valor(p)), fillOpacity: dentro ? 1 : 0.15, color: s ? css('--accent') : bord, weight: s ? 3.5 : 0.8 });
      el.tabIndex = dentro ? 0 : -1;
      el.setAttribute('aria-label', p.nome + ': ' + fmtValor(valor(p)));
    });
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
  function enquadrar() {
    const ls = C.F.filter(f => noRecorte(f.properties)).map(f => porCamada[f.properties.cod]);
    const b = L.latLngBounds([]); ls.forEach(l => b.extend(l.getBounds()));
    const big = innerWidth > 860;
    map.fitBounds(b, { paddingTopLeft: [20, 60], paddingBottomRight: [big ? (S.sel ? 380 : 300) : 20, big ? 20 : (S.sel ? 320 : 20)] });
  }
  function legenda() {
    let h = '<b>' + C.NOME_IND[S.ind] + '</b><div style="color:var(--ink-3);margin:-4px 0 6px">' + C.TIPOS[S.tipo] + ' · ' + C.nomePer(S.per) + '</div>';
    CL.rot.forEach((r, i) => { h += '<div class="row"><span class="sw" style="background:' + css(CL.cores[i]) + '"></span>' + r + '</div>'; });
    if (S.ind === 'taxa') h += '<small>Média do estado: ' + nf(C.taxaEstado(S.tipo, S.per), 1) + ' por 100 mil/ano.' + (S.reg ? ' Média da ' + esc(nomeReg(S.reg)) + ': ' + nf(C.taxaRegiao(S.reg, S.tipo, S.per), 1) + '.' : '') + ' Cada cor reúne cerca de 1/5 dos municípios.</small>';
    if (S.ind === 'oe') h += '<small>1 = o município notifica na mesma proporção que o estado.</small>';
    if (S.ind === 'casos') h += '<small>Estado: ' + nf(C.casosEstado(S.tipo, S.per)) + ' casos.</small>';
    if (S.ind !== 'casos') h += '<small>Com menos de 10 casos no período, o valor é instável.</small>';
    $('leg').innerHTML = h;
  }
  function ranking() {
    const todos = C.F.map(f => f.properties).filter(noRecorte);
    let lst, nota;
    if (S.rk === 'maiores') {
      lst = todos.sort((a, b) => valor(b) - valor(a)).slice(0, 10);
      nota = '* menos de 10 casos no período escolhido: valor instável. Escolha um município aqui, no mapa, na busca ou na tabela para ver a ficha.';
    } else {
      lst = todos.filter(p => casosSel(p) >= MIN_CASOS).sort((a, b) => valor(a) - valor(b)).slice(0, 10);
      nota = 'Só municípios com pelo menos 10 casos no tipo e período escolhidos: com menos, um único caso muda muito o valor e o município pareceria "o menor" por acaso.';
    }
    $('rk').innerHTML = lst.map(p => '<li><a href="#mapa-' + p.cod + '" tabindex="0">' + esc(p.nome) + '</a> — ' + fmtValor(valor(p)) + (casosSel(p) < MIN_CASOS ? ' *' : '') + '</li>').join('') || '<li>Nenhum município com 10 casos ou mais neste filtro.</li>';
    $('rknota').textContent = (S.reg ? 'Só municípios da ' + nomeReg(S.reg) + '. ' : '') + nota;
    document.querySelectorAll('.rktabs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.r === S.rk)));
    $('rk').setAttribute('aria-label', S.rk === 'maiores' ? '10 maiores valores' : '10 menores valores, só municípios com pelo menos 10 casos');
  }
  function tabelaMapa() {
    if (!S.tabela) return;
    const linhas = C.F.map(f => f.properties).filter(noRecorte).sort((a, b) => valor(b) - valor(a));
    const at = k => (S.ind === k ? ' class="ativo"' : '');
    $('maptab').innerHTML = '<table><caption class="sr">' + esc(filtrosTexto()) + '</caption><thead><tr><th>Município</th><th>Mulheres</th><th' + at('casos') + '>Casos</th><th' + at('taxa') +
      '>Taxa / 100 mil / ano</th><th' + at('oe') + '>Observado ÷ esperado</th></tr></thead><tbody>' +
      linhas.map(p => '<tr data-c="' + p.cod + '" tabindex="0"><td>' + esc(p.nome) + (casosSel(p) < MIN_CASOS ? ' *' : '') + '</td><td>' + nf(p.pop) + '</td><td' + at('casos') + '>' + nf(casosSel(p)) + '</td><td' + at('taxa') + '>' +
        nf(C.taxa(p, S.tipo, S.per), 1) + '</td><td' + at('oe') + '>' + nf(C.oe(p, S.tipo, S.per), 2) + '</td></tr>').join('') +
      '</tbody></table><p class="hint" style="margin-top:8px">' + (S.reg ? nf(linhas.length) + ' municípios da ' + esc(nomeReg(S.reg)) + '. ' : '') + 'Mesmos valores e filtros do mapa, ordenados pelo indicador escolhido. * menos de 10 casos no período: valor instável.</p>';
  }
  function atualizar() {
    $('indhint').textContent = HINT[S.ind];
    $('mapatitulo').textContent = filtrosTexto();
    estilizar(); legenda(); ranking(); tabelaMapa();
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
    }).join('') + '</div>' + (ref ? '<div class="leg-ref">Barra: % do município · traço preto: % do estado</div>' : '');
  }
  // Frase com a faixa etária mais atingida (empates aparecem juntos; a faixa "Ignorada" não entra)
  function faixaTopo(p) {
    const tot = p.faixa.reduce((a, b) => a + b, 0), conhecidas = p.faixa.slice(0, 10), mx = Math.max(...conhecidas);
    if (!tot || !mx) return '<p class="fxtop">Nenhum caso com idade informada.</p>';
    const nomes = C.FX.slice(0, 10).map((f, i) => [f, conhecidas[i]]).filter(x => x[1] === mx).map(x => x[0] === '<1 Ano' ? 'menos de 1 ano' : C.rotFx(x[0]) + ' anos');
    return '<p class="fxtop">Faixa mais atingida: <b>' + nomes.join(' e ') + '</b> (' + nf(mx) + (nomes.length > 1 ? ' casos cada, ' : ' casos, ') + nf(100 * mx / tot, 0) + '%' + (nomes.length > 1 ? ' cada' : '') + ').</p>';
  }
  function htmlFicha(p) {
    const t = S.tipo, per = S.per, c = C.casos(p, t, per), ce = C.casosEstado(t, per), tx = C.taxa(p, t, per), te = C.taxaEstado(t, per);
    const e = C.esperado(p, t, per), o = c / e, totEst = C.casosEstado('total', per);
    const tiposP = ['fisica', 'psicologica', 'sexual'].map(k => [C.TIPOS[k], C.casos(p, k, per)]);
    const totP = C.casos(p, 'total', per);
    const refTipos = ['fisica', 'psicologica', 'sexual'].map(k => C.casosEstado(k, per) / totEst);
    let h = '<button class="x noprint" type="button" aria-label="Fechar ficha">×</button><h2>' + esc(p.nome) + '</h2>' +
      '<div class="sub">' + nf(p.pop) + ' mulheres (Censo 2022) · ' + C.TIPOS[t] + ' · ' + C.nomePer(per) +
      (C.REG[p.reg] ? '<br>' + esc(nomeReg(p.reg)) + ' · ' + esc(C.REG[p.reg].macro) : '') + '</div>';
    if (c < MIN_CASOS) h += '<div class="flag">Poucos casos (' + nf(c) + ' no tipo e período escolhidos). Com números tão pequenos, um caso a mais ou a menos muda muito a taxa e o observado ÷ esperado.</div>';
    h += '<div class="ind5">' +
      '<div class="it"><div class="cab"><span>Casos notificados</span>' + linkCalc('casos') + '</div><div class="v">' + nf(c) + '</div><div class="c">Estado: ' + nf(ce) + ' (' + nf(100 * c / ce, 1) + '% do estado; ' + nf(100 * p.pop / C.POP, 1) + '% das mulheres)</div></div>' +
      '<div class="it"><div class="cab"><span>Taxa por 100 mil mulheres por ano</span>' + linkCalc('taxa') + '</div><div class="v">' + nf(tx, 1) + '</div><div class="c">Média do estado: ' + nf(te, 1) +
        (C.REG[p.reg] ? '<br>Média da região de saúde (' + esc(nomeReg(p.reg)) + '): ' + nf(C.taxaRegiao(p.reg, t, per), 1) : '') + '</div></div>' +
      '<div class="it"><div class="cab"><span>Observado ÷ esperado</span>' + linkCalc('oe') + '</div><div class="v">' + nf(o, 2) + '</div><div class="c">Esperado se seguisse o estado: ' + nf(e, 1) + ' casos · ' + C.leituraOE(o) + ' (estado = 1)</div></div>' +
      '<div class="it"><div class="cab"><span>Tipos de violência (' + C.nomePer(per) + ')</span>' + linkCalc('tipos') + '</div>' + barras(tiposP, totP ? refTipos : null) +
      '<div class="c">Total de notificações: ' + nf(totP) + '. Uma notificação pode ter mais de um tipo.</div></div>' +
      '<div class="it"><div class="cab"><span>Faixa etária (2019 a 2024, todos os tipos)</span>' + linkCalc('faixa') + '</div>' + faixaTopo(p) +
      barras(C.FX.map((f, i) => [C.rotFx(f), p.faixa[i]]), p.faixa.some(v => v) ? C.faixaEstado.map(v => v / C.casosEstado('total', 'all')) : null) + '</div>' +
      '</div>';
    h += '<h3>Casos por ano (' + C.TIPOS[t] + ')</h3>' + barras(C.ANOS.map((a, i) => [String(a), p.casos[t][i]]));
    h += '<div class="btnrow noprint"><button class="btn peq pri" type="button" data-acao="imprimir">Imprimir ficha</button>' +
      '<button class="btn peq" type="button" data-acao="link">Copiar link</button><button class="btn peq" type="button" data-acao="comparar">Comparar com outros</button></div>';
    return h;
  }
  function ficha() {
    const p = C.porCod[S.sel], el = $('painel');
    el.innerHTML = htmlFicha(p); el.style.display = 'block';
    el.querySelector('.x').addEventListener('click', () => { location.hash = '#mapa'; });
    el.querySelector('[data-acao=imprimir]').addEventListener('click', imprimirFicha);
    el.querySelector('[data-acao=link]').addEventListener('click', () => WS.util.copiar(location.href.split('#')[0] + '#mapa-' + p.cod, 'Link da ficha copiado'));
    el.querySelector('[data-acao=comparar]').addEventListener('click', () => abrirComparar([p.cod]));
  }
  let voltarFoco = null;
  function mostrarFicha(cod, { focar = false } = {}) {
    if (!C.porCod[cod]) return false;
    if (!S.sel && document.activeElement && document.activeElement !== document.body && !$('painel').contains(document.activeElement)) voltarFoco = document.activeElement;
    S.sel = cod;
    if (S.tabela) alternarTabela(false);
    const l = porCamada[cod], big = innerWidth > 860;
    map.fitBounds(l.getBounds(), { maxZoom: 8.5, paddingTopLeft: [40, 60], paddingBottomRight: [big ? 400 : 40, big ? 40 : 320] });
    estilizar(); ficha();
    if (focar) $('painel').querySelector('h2').setAttribute('tabindex', '-1'), $('painel').querySelector('h2').focus();
    return true;
  }
  function fecharFicha() {
    const estavaNaFicha = $('painel').contains(document.activeElement);
    S.sel = null; $('painel').style.display = 'none'; $('painel').innerHTML = ''; estilizar();
    if (estavaNaFicha || voltarFoco) { const alvo = voltarFoco && document.contains(voltarFoco) && voltarFoco.getClientRects().length ? voltarFoco : $('mapatitulo'); alvo.focus({ preventScroll: true }); }
    voltarFoco = null;
  }

  // Imprimir ficha: monta uma folha limpa em #impressao (só a ficha, com filtros, fonte e data)
  function imprimirFicha() {
    const p = C.porCod[S.sel], hoje = new Date().toLocaleDateString('pt-BR');
    $('impressao').innerHTML = '<div class="ficha"><div style="font-size:10pt;color:#444">Violência contra a mulher na Paraíba · ficha do município</div>' + htmlFicha(p) +
      '<div class="rodape">Fonte: SINAN/TABNET (notificações de mulheres, município de residência, sem violência autoprovocada) e Censo 2022 (IBGE). ' +
      'Os números mostram casos notificados, não todos os que acontecem. Impresso em ' + hoje + '. Endereço: ' + esc(location.href.split('#')[0] + '#mapa-' + p.cod) + '</div></div>';
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

  /* ---------- início ---------- */
  function iniciar(calc) {
    C = calc;
    map = L.map('map', { zoomSnap: 0.25, attributionControl: false, keyboard: true }).setView([-7.12, -36.8], 7.5);
    tip = $('tip');
    const alfabetica = [...C.F].sort((a, b) => a.properties.nome.localeCompare(b.properties.nome, 'pt'));
    ORDEM = alfabetica.map(f => f.properties.cod);
    camada = L.geoJSON({ type: 'FeatureCollection', features: alfabetica }, { style: () => ({}), onEachFeature: (f, l) => {
      const cod = f.properties.cod;
      porCamada[cod] = l;
      l.on('mousemove', e => {
        if (ponteiro === 'touch') return;
        tip.style.display = 'block'; tip.textContent = f.properties.nome + ' · ' + fmtValor(valor(f.properties));
        tip.style.left = (e.originalEvent.clientX + 14) + 'px'; tip.style.top = (e.originalEvent.clientY - 34) + 'px';
        destacar(l);
      });
      l.on('mouseout', () => { if (ponteiro !== 'touch') { esconderDica(); estilizar(); } });
      // toque: o 1º toque mostra a etiqueta acima do município; o 2º no mesmo município abre a ficha
      l.on('click', e => {
        L.DomEvent.stopPropagation(e);
        if (ponteiro === 'touch' && dicaCod !== cod) { estilizar(); destacar(l); dicaPerto(l, 'Toque de novo para abrir a ficha', 'toque'); dicaCod = cod; return; }
        esconderDica(); location.hash = '#mapa-' + cod;
      });
    } }).addTo(map);
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
    map.fitBounds(camada.getBounds(), { padding: [10, 10] });

    $('per').innerHTML = '<option value="all">2019 a 2024 (soma)</option>' + C.ANOS.map(a => '<option value="' + a + '">' + a + '</option>').join('');
    ['ind', 'tipo', 'per'].forEach(id => $(id).addEventListener('change', e => { S[id] = e.target.value; atualizar(); }));
    const porMacro = {};
    Object.entries(C.REG).forEach(([cod, r]) => (porMacro[r.macro] = porMacro[r.macro] || []).push(cod));
    $('reg').innerHTML = '<option value="">Todo o estado</option>' + Object.keys(porMacro).sort().map(m => '<optgroup label="' + esc(m) + '">' +
      porMacro[m].map(c => '<option value="' + c + '">' + esc(C.REG[c].nome) + ' (' + C.munsRegiao(c).length + ' municípios)</option>').join('') + '</optgroup>').join('');
    $('reg').addEventListener('change', e => { S.reg = e.target.value; atualizar(); enquadrar(); });
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
    return { S, mostrarFicha, fecharFicha, abrirComparar, imprimirFicha, alternarTabela, redesenhar: () => { estilizar(); legenda(); }, invalidar: () => map.invalidateSize(),
      limitesMapa: () => map.getBounds() };
  }
  return { iniciar };
})();
