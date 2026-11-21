/* analise.js: tela Análise (números do estado, leituras, gráficos, tabela dos municípios e "Baixar CSV"). */
"use strict";
window.WS = window.WS || {};
WS.analise = (function () {
  const { $, nf, css, esc, semAc } = WS.util;
  let C;
  const tip = () => $('tip');
  function tipShow(e, txt) { const t = tip(); t.style.display = 'block'; t.textContent = txt; t.style.left = (e.clientX + 14) + 'px'; t.style.top = (e.clientY - 34) + 'px'; }
  function tipHide() { tip().style.display = 'none'; }

  function numeros() {
    const tot = C.casosEstado('total', 'all'), serie = t => C.ANOS.map((a, i) => C.F.reduce((s, f) => s + f.properties.casos[t][i], 0));
    const st = serie('total'), sx = serie('sexual'), fx = C.faixaEstado, props = C.F.map(f => f.properties);
    const comMais = [...props].sort((a, b) => C.casos(b, 'total', 'all') - C.casos(a, 'total', 'all')), jp = comMais[0];
    const grandes = props.filter(p => C.casos(p, 'total', 'all') >= 10);
    const muitoAbaixo = grandes.filter(p => C.oe(p, 'total', 'all') < 0.5).sort((a, b) => C.oe(a, 'total', 'all') - C.oe(b, 'total', 'all'));
    const muitoAcima = grandes.filter(p => C.oe(p, 'total', 'all') >= 2), poucos = props.filter(p => C.casos(p, 'total', 'all') < 10).length;
    const pct = (a, b) => nf(100 * a / b, 1) + '%';
    $('kpis').innerHTML = [
      [nf(tot), 'casos notificados, 2019 a 2024'],
      [nf(C.taxaEstado('total', 'all'), 1), 'por 100 mil mulheres por ano, estado'],
      [(st[5] > st[0] ? '+' : '') + nf(100 * (st[5] / st[0] - 1), 0) + '%', 'variação dos casos, 2019 a 2024'],
      [nf(poucos), 'municípios com menos de 10 casos']
    ].map(k => '<div class="kpi"><div class="n">' + k[0] + '</div><div class="l">' + k[1] + '</div></div>').join('');
    // contextos: faixa de maior taxa, local de atendimento e serviços declarados (MUNIC 2023)
    const txFx = C.FX.slice(0, C.N_FX_TAXA).map((_, i) => C.taxaFaixaEstado(i)), iMaxTx = txFx.indexOf(Math.max(...txFx));
    const iMaxCasos = fx.slice(0, C.N_FX_TAXA).indexOf(Math.max(...fx.slice(0, C.N_FX_TAXA))), rotF = i => C.rotFx(C.FX[i]) + ' anos';
    const loc = C.localEstado, pL = k => nf(C.pctLocal(loc, k), 1) + '%';
    const SERV = [['organismo_politicas_mulheres', 'organismo de políticas para mulheres'], ['centro_referencia', 'centro de referência'], ['casa_abrigo', 'casa-abrigo ou acolhimento'], ['delegacia_mulher', 'delegacia especializada']];
    const nServ = k => props.filter(p => p.rede[k] === 'Sim').length, nSemDado = k => props.filter(p => p.rede[k] === '-').length;
    const servTxt = SERV.map(([k, n]) => '<b>' + nf(nServ(k)) + '</b> declaram ' + n).join('; ');
    const servOrd = [...SERV].sort((x, y) => nServ(y[0]) - nServ(x[0]));
    const semDado = SERV.filter(([k]) => nSemDado(k)).map(([k, n]) => '<b>' + nf(nSemDado(k)) + '</b> sem dado sobre ' + n).join('; ');
    const b = x => '<b>' + x + '</b>';
    const L = [
      ['As notificações cresceram de 2019 a 2024, com queda em 2020.', 'Foram ' + b(nf(st[0])) + ' casos em 2019, ' + b(nf(st[1])) + ' em 2020 e ' + b(nf(st[5])) + ' em 2024. A queda de 2020 coincide com a pandemia. O dado não separa aumento da violência de aumento da notificação.', 'O aumento acompanhou a abertura de serviços que notificam?'],
      ['A violência física é a mais notificada; a sexual foi a que mais cresceu.', 'A física aparece em ' + b(pct(C.casosEstado('fisica', 'all'), tot)) + ' das notificações. A sexual passou de ' + b(nf(sx[0])) + ' casos em 2019 para ' + b(nf(sx[5])) + ' em 2024 (' + b('+' + nf(100 * (sx[5] / sx[0] - 1), 0) + '%') + ').', 'O atendimento à violência sexual acompanhou esse crescimento?'],
      ['Meninas e mulheres jovens concentram os casos.', 'De 20 a 39 anos: ' + b(pct(fx[5] + fx[6], tot)) + ' dos casos. De 10 a 19 anos: ' + b(pct(fx[3] + fx[4], tot)) + '. Até 9 anos: ' + b(pct(fx[0] + fx[1] + fx[2], tot)) + '.', 'A escola e a rede de proteção à criança e ao adolescente participam da notificação?'],
      ['Os casos se concentram nos municípios maiores.', esc(jp.nome) + ' tem ' + b(pct(C.casos(jp, 'total', 'all'), tot)) + ' dos casos e ' + b(pct(jp.pop, C.POP)) + ' das mulheres do estado (observado ÷ esperado: ' + b(nf(C.oe(jp, 'total', 'all'), 2)) + '). Os 5 municípios com mais casos somam ' + b(pct(comMais.slice(0, 5).reduce((s, p) => s + C.casos(p, 'total', 'all'), 0), tot)) + '.', 'A rede da capital atende mulheres de outros municípios?'],
      [nf(muitoAbaixo.length) + ' municípios notificam menos da metade do esperado.', 'São ' + b(nf(muitoAbaixo.length)) + ' entre os ' + b(nf(grandes.length)) + ' municípios com pelo menos 10 casos. O menor valor é o de ' + esc(muitoAbaixo[0].nome) + ' (' + b(nf(C.oe(muitoAbaixo[0], 'total', 'all'), 2)) + ').', 'O que dificulta a notificação nesses municípios: acesso, formação das equipes ou receio de expor a mulher?'],
      [nf(muitoAcima.length) + ' municípios notificam o dobro ou mais do esperado.', 'Entre os ' + b(nf(grandes.length)) + ' municípios com pelo menos 10 casos, ' + b(nf(muitoAcima.length)) + ' têm observado ÷ esperado de 2 ou mais. Podem ter mais violência ou uma rede que registra melhor.', 'O que esses municípios fazem que pode ser levado a outros?'],
      [nf(poucos) + ' municípios têm menos de 10 casos em 6 anos.', 'Nesses ' + b(nf(poucos)) + ' municípios, um único caso muda muito a taxa e o observado ÷ esperado. O painel marca esses valores com *.', 'Faz sentido acompanhá-los em conjunto, por região de saúde?'],
      ['Em taxa, a faixa etária mais atingida é ' + rotF(iMaxTx) + '.', 'São ' + b(nf(C.taxaFaixaEstado(iMaxTx), 1)) + ' casos por ano a cada 100 mil meninas dessa idade, a maior taxa entre as faixas. Em número de casos, a maior é ' + rotF(iMaxCasos) + ' (' + b(nf(fx[iMaxCasos])) + ' casos; ' + b(nf(C.taxaFaixaEstado(iMaxCasos), 1)) + ' por 100 mil/ano).', 'Que serviços chegam hoje a essa faixa etária: escola, conselho tutelar, atenção básica?'],
      ['A maior parte das notificações foi feita na própria região de saúde.', b(pL(0)) + ' das notificações foram feitas na região de saúde onde a mulher mora, ' + b(pL(1)) + ' em outra região da Paraíba e ' + b(pL(2)) + ' fora do estado (' + b(nf(loc[2])) + ' casos).', 'Nas regiões de onde mais mulheres saem para ser atendidas, falta serviço local ou há referência regional pactuada?'],
      ['Na MUNIC 2023, o serviço mais declarado é ' + servOrd[0][1] + '; o menos declarado, ' + servOrd[servOrd.length - 1][1] + '.', 'Dos ' + b(nf(props.length)) + ' municípios, ' + servTxt + '.' + (semDado ? ' Há ' + semDado + '.' : '') + ' São declarações das prefeituras, não um cadastro oficial.', 'Onde não há serviço declarado, para onde a mulher é encaminhada?']
    ];
    // cada resultado: um parágrafo (frase-título + evidência, números em negrito) e a pergunta para a gestão em texto normal
    $('concl').innerHTML = L.map(c => '<li><p>' + c[0] + ' ' + c[1] + '</p>' + (c[2] ? '<p class="perg">Para a gestão: ' + c[2] + '</p>' : '') + '</li>').join('');
    return { st, sx, serie, tot };
  }

  /* gráficos SVG */
  function linhas(el, series) {
    const W = 560, H = 280, m = { l: 46, r: 118, t: 12, b: 28 }, w = W - m.l - m.r, h = H - m.t - m.b;
    const mx = Math.ceil(Math.max(...series.flatMap(s => s.v)) / 500) * 500, x = i => m.l + i * w / (C.ANOS.length - 1), y = v => m.t + h - v / mx * h;
    let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Casos por ano e tipo: ' + series.map(se => se.n + ' ' + se.v.map(v => nf(v)).join(', ')).join('; ') + '">';
    for (let g = 0; g <= mx; g += 500) s += '<line x1="' + m.l + '" x2="' + (m.l + w) + '" y1="' + y(g) + '" y2="' + y(g) + '" stroke="var(--line)"/><text x="' + (m.l - 6) + '" y="' + (y(g) + 4) + '" text-anchor="end">' + nf(g) + '</text>';
    C.ANOS.forEach((a, i) => { s += '<text x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle">' + a + '</text>'; });
    series.forEach(se => {
      s += '<polyline fill="none" stroke="' + se.c + '" stroke-width="2" points="' + se.v.map((v, i) => x(i) + ',' + y(v)).join(' ') + '"/>';
      se.v.forEach((v, i) => { s += '<circle cx="' + x(i) + '" cy="' + y(v) + '" r="4" fill="' + se.c + '" stroke="var(--surface)" stroke-width="2"/>'; });
      s += '<text x="' + (x(5) + 8) + '" y="' + (y(se.v[5]) + 4) + '" class="val">' + se.n + '</text>';
    });
    C.ANOS.forEach((a, i) => { s += '<rect x="' + (x(i) - w / 10) + '" y="' + m.t + '" width="' + (w / 5) + '" height="' + h + '" fill="transparent" data-i="' + i + '"/>'; });
    el.innerHTML = s + '</svg>';
    el.querySelectorAll('rect[data-i]').forEach(r => { r.addEventListener('mousemove', e => { const i = +r.dataset.i; tipShow(e, C.ANOS[i] + ': ' + series.map(se => se.n + ' ' + nf(se.v[i])).join(' · ')); }); r.addEventListener('mouseleave', tipHide); });
  }
  function barras(el, pares, cor, extra, ref, unidade) {   // ref = { v, rot }: linha de referência (ex.: taxa geral do estado)
    const W = 600, lh = 26, m = { l: 110, r: 250 }, H = pares.length * lh + 8 + (ref ? 18 : 0), w = W - m.l - m.r, mx = Math.max(...pares.map(p => p[1]), ref ? ref.v : 0);
    const dec = unidade ? 1 : 0, un = unidade || ' casos';
    let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + pares.map(p => p[0] + ' ' + nf(p[1], dec)).join('; ') + (ref ? '; ' + ref.rot : '') + '">';
    if (ref) { const x = m.l + ref.v / mx * w, yb = 4 + pares.length * lh; s += '<line x1="' + x + '" x2="' + x + '" y1="2" y2="' + yb + '" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="4 3"/><text x="' + x + '" y="' + (yb + 13) + '" text-anchor="middle" class="val">' + ref.rot + '</text>'; }
    const halo = ref ? ' style="paint-order:stroke;stroke:var(--surface);stroke-width:4px"' : '';   // número legível sobre a linha de referência
    pares.forEach((p, i) => {
      const y = 4 + i * lh, bw = Math.max(2, p[1] / mx * w);
      s += '<text x="' + (m.l - 8) + '" y="' + (y + 15) + '" text-anchor="end">' + p[0] + '</text><rect x="' + m.l + '" y="' + (y + 4) + '" width="' + bw + '" height="16" rx="4" fill="' + cor + '" data-t="' + p[0] + ': ' + nf(p[1], dec) + un + '"/><text x="' + (m.l + bw + 6) + '" y="' + (y + 16) + '" class="val"' + halo + '>' + nf(p[1], dec) + (extra ? extra(p, i) : '') + '</text>';
    });

    el.innerHTML = s + '</svg>';
    el.querySelectorAll('rect[data-t]').forEach(r => { r.addEventListener('mousemove', e => tipShow(e, r.dataset.t)); r.addEventListener('mouseleave', tipHide); });
  }
  let N, modoFx = 'casos';
  // Faixa etária na Análise: Casos ou Taxa por 100 mil/ano (com a taxa geral do estado como referência)
  function faixaAnalise() {
    document.querySelectorAll('#fxAnalise [data-fxa]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.fxa === modoFx)));
    if (modoFx === 'casos') {
      $('fxdesc').textContent = 'Paraíba, 2019 a 2024, todos os tipos.';
      barras($('g-faixa'), C.FX.map((f, i) => [C.rotFx(f), C.faixaEstado[i]]), css('--s1'), p => ' casos (' + nf(100 * p[1] / N.tot, 1) + '%)');
    } else {
      const te = C.taxaEstado('total', 'all'), ign = C.faixaEstado[C.N_FX_TAXA];
      $('fxdesc').textContent = 'Paraíba, 2019 a 2024. Casos por ano a cada 100 mil mulheres da faixa (Censo 2022). Linha tracejada: taxa geral do estado (' + nf(te, 1) + '). A faixa "Ignorada" (' + nf(ign) + ' casos) não tem taxa.';
      barras($('g-faixa'), C.FX.slice(0, C.N_FX_TAXA).map((f, i) => [C.rotFx(f), C.taxaFaixaEstado(i)]), css('--s1'),
        (p, i) => ' por 100 mil/ano' + (C.faixaEstado[i] < 10 ? ' *' : '') + ' · ' + nf(C.faixaEstado[i]) + ' casos', { v: te, rot: 'estado: ' + nf(te, 1) + ' por 100 mil/ano' }, ' por 100 mil/ano');
    }
  }
  // Onde as mulheres foram atendidas (estado): frase-resumo e barra calculadas dos dados
  function localAnalise() {
    const v = C.localEstado, p = k => nf(C.pctLocal(v, k), 1) + '%';
    $('localfrase').textContent = p(0) + ' foram atendidas na própria região de saúde, ' + p(1) + ' em outra região da Paraíba e ' + p(2) + ' fora do estado (' + nf(v[2]) + ' casos).';
    $('g-local').innerHTML = WS.util.barra100(C.LOCAIS.map((r, k) => ({ rot: r, n: v[k], cor: css(['--s1', '--s2', '--s4'][k]), k: k + 1 })));
  }
  function graficos() {
    localAnalise();
    const tipos = Object.keys(C.TIPOS);
    linhas($('g-serie'), [{ n: 'Todos', v: N.st, c: css('--s1') }, { n: 'Física', v: N.serie('fisica'), c: css('--s2') }, { n: 'Psicológica', v: N.serie('psicologica'), c: css('--s3') }, { n: 'Sexual', v: N.sx, c: css('--s4') }]);
    faixaAnalise();
    barras($('g-tipo'), tipos.map(k => [C.TIPOS[k], C.casosEstado(k, 'all')]), css('--s1'), (p, i) => ' casos · ' + nf(C.taxaEstado(tipos[i], 'all'), 1) + ' por 100 mil/ano');
  }

  /* tabela + CSV */
  const T = { k: 'casos', desc: true };
  const linhasTabela = t => C.F.map(f => { const p = f.properties; return { cod: p.cod, nome: p.nome, pop: p.pop, casos: C.casos(p, t, 'all'), taxa: C.taxa(p, t, 'all'), esperado: C.esperado(p, t, 'all'), oe: C.oe(p, t, 'all'), pouco: C.casos(p, t, 'all') < 10 }; });
  function tabela() {
    const t = $('ttipo').value, q = semAc($('tbusca').value);
    const rows = linhasTabela(t).filter(r => !q || semAc(r.nome).includes(q));
    rows.sort((a, b) => { const va = a[T.k], vb = b[T.k]; return (typeof va === 'string' ? va.localeCompare(vb, 'pt') : va - vb) * (T.desc ? -1 : 1); });
    $('tab').querySelector('tbody').innerHTML = rows.map(r => '<tr data-c="' + r.cod + '" tabindex="0"><td>' + esc(r.nome) + (r.pouco ? ' <span title="Menos de 10 casos: valores instáveis" style="color:var(--warn-ink)">*</span>' : '') + '</td><td>' + nf(r.pop) + '</td><td>' + nf(r.casos) + '</td><td>' + nf(r.taxa, 1) + '</td><td>' + nf(r.oe, 2) + '</td></tr>').join('') +
      (rows.length ? '' : '<tr><td colspan="5" class="vazio">Nenhum município encontrado para "' + esc($('tbusca').value.trim()) + '". Confira o nome (acentos e maiúsculas não importam).</td></tr>') +
      '<tr><td colspan="5" style="text-align:left;color:var(--ink-3)">* menos de 10 casos em 6 anos: taxa e observado ÷ esperado instáveis.</td></tr>';
    $('tab').querySelectorAll('th').forEach(th => {
      th.textContent = th.textContent.replace(/ [▲▼]$/, '') + (th.dataset.k === T.k ? (T.desc ? ' ▼' : ' ▲') : '');
      th.setAttribute('aria-sort', th.dataset.k === T.k ? (T.desc ? 'descending' : 'ascending') : 'none');
    });
  }
  // CSV dos 223 municípios (tipo escolhido, 2019 a 2024), separador ";" e vírgula decimal para abrir direto no Excel/Calc
  function csv() {
    const t = $('ttipo').value, dec = (v, d) => v.toFixed(d).replace('.', ',');
    const cab = 'cod_ibge7;municipio;mulheres_censo2022;casos_2019_2024;taxa_100mil_mulheres_ano;casos_esperados;observado_sobre_esperado';
    const linhas = linhasTabela(t).sort((a, b) => a.cod.localeCompare(b.cod)).map(r => [r.cod, '"' + r.nome.replace(/"/g, '""') + '"', r.pop, r.casos, dec(r.taxa, 4), dec(r.esperado, 4), dec(r.oe, 4)].join(';'));
    WS.util.baixar('violencia_mulher_pb_' + t + '_2019-2024.csv', '﻿' + cab + '\r\n' + linhas.join('\r\n') + '\r\n', 'text/csv;charset=utf-8');
  }

  function iniciar(calc) {
    C = calc; N = numeros(); graficos(); tabela();
    const ordenar = k => { T.desc = T.k === k ? !T.desc : k !== 'nome'; T.k = k; tabela(); };
    $('tab').querySelector('thead').addEventListener('click', e => { const k = e.target.dataset.k; if (k) ordenar(k); });
    $('tab').querySelector('thead').addEventListener('keydown', e => { const k = e.target.dataset.k; if (k && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); ordenar(k); } });
    const irMun = tr => { if (tr) location.hash = '#mapa-' + tr.dataset.c; };
    $('tab').querySelector('tbody').addEventListener('click', e => irMun(e.target.closest('tr[data-c]')));
    $('tab').querySelector('tbody').addEventListener('keydown', e => { if (e.key === 'Enter') irMun(e.target.closest('tr[data-c]')); });
    $('ttipo').addEventListener('change', tabela); $('tbusca').addEventListener('input', tabela);
    $('baixarCsv').addEventListener('click', csv);
    document.querySelectorAll('#fxAnalise [data-fxa]').forEach(b => b.addEventListener('click', () => { modoFx = b.dataset.fxa; faixaAnalise(); }));
    return { graficos, csv };
  }
  return { iniciar };
})();
