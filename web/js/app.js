/* app.js: liga os módulos. Abas e endereço por tela e por município:
   #mapa, #analise, #como-calcular e #mapa-<cod_ibge7> (abre a ficha). O endereço pode ser copiado e enviado. */
"use strict";
window.WS = window.WS || {};
(function () {
  const { $ } = WS.util;
  let mapa, analise = null, C, indAlvo = null, comoCalcularPronto = false;

  const NOME_SITE = 'Violência contra a mulher PB';
  const TITULOS = { mapa: 'Mapa', analise: 'Análise', 'como-calcular': 'Como calcular' };
  function abrirTela(v) {
    document.title = TITULOS[v] + ' · ' + NOME_SITE;
    document.querySelectorAll('.tabs button[data-v]').forEach(b => { const on = b.dataset.v === v; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; });
    // Análise e Como calcular só são montadas quando abertas pela primeira vez (a abertura do painel fica mais leve)
    if (v === 'analise' && !analise) analise = WS.analise.iniciar(C);
    if (v === 'como-calcular' && !comoCalcularPronto) { WS.calculo.telaComoCalcular(C, $('indtxt')); comoCalcularPronto = true; }
    document.querySelectorAll('.view').forEach(s => s.classList.toggle('on', s.id === 'v-' + v));
    if (v === 'mapa') setTimeout(() => mapa.invalidar(), 50);
  }
  // Lê o endereço (#...) e mostra a tela/ficha correspondente
  function rota() {
    const h = decodeURIComponent(location.hash.slice(1)) || 'mapa';
    let m;
    if (h === 'analise') abrirTela('analise');
    else if (h === 'como-calcular') {
      abrirTela('como-calcular');
      const alvo = indAlvo && document.getElementById('ind-' + indAlvo);
      document.querySelectorAll('.ind article.alvo').forEach(a => a.classList.remove('alvo'));
      if (alvo) { alvo.classList.add('alvo'); alvo.scrollIntoView({ block: 'start' }); alvo.focus({ preventScroll: true }); }
      else $('v-como-calcular').querySelector('.scroll').scrollTop = 0;
      indAlvo = null;
    } else if ((m = h.match(/^mapa-(\d{7})$/)) && C.porCod[m[1]]) {
      abrirTela('mapa');
      document.title = C.porCod[m[1]].nome + ' · ' + NOME_SITE;
      if (mapa.S.sel !== m[1]) setTimeout(() => mapa.mostrarFicha(m[1], { focar: true }), 60);
    } else {
      abrirTela('mapa');
      if (mapa.S.sel) mapa.fecharFicha();
    }
  }

  // Preferências guardadas no navegador (podem falhar em modo privado ou com o armazenamento bloqueado)
  const CHAVE_SOBRE = 'websig-sobre-visto';
  const lerPref = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const gravarPref = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* sem armazenamento: o aviso volta na próxima visita */ } };
  // Sobre o painel: abre na primeira visita sem esperar os dados (menos quando se chega por link de uma ficha) e pelo botão do topo
  const sobre = $('sobre');
  let tour = null, tourPedido = false;
  const abrirTour = () => { if (tour) tour.abrir(); else tourPedido = true; };
  const fecharSobre = () => { gravarPref(CHAVE_SOBRE, '1'); if (sobre.open) sobre.close(); };
  $('abrirSobre').addEventListener('click', () => sobre.showModal());
  ['sobreFechar', 'sobreComecar'].forEach(id => $(id).addEventListener('click', fecharSobre));
  sobre.addEventListener('close', () => gravarPref(CHAVE_SOBRE, '1'));
  $('abrirTour').addEventListener('click', abrirTour);
  $('sobreTour').addEventListener('click', () => { fecharSobre(); abrirTour(); });
  if (!lerPref(CHAVE_SOBRE) && !/^#mapa-\d{7}$/.test(location.hash)) sobre.showModal();

  WS.dados.carregar((DADOS, origem) => {
    const carregando = $('carregando'); if (carregando) carregando.remove();
    C = WS.calculo.criar(DADOS);
    mapa = WS.mapa.iniciar(C);
    document.querySelectorAll('.tabs button[data-v]').forEach(b => b.addEventListener('click', () => {
      const alvo = '#' + b.dataset.v;
      if (location.hash === alvo) rota(); else location.hash = alvo;
    }));
    const abas = [...document.querySelectorAll('.tabs button[data-v]')];
    abas.forEach((b, i) => b.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      e.preventDefault(); const alvo = abas[(i + d + abas.length) % abas.length]; alvo.focus(); alvo.click();
    }));
    // links "como calcular" ao lado de cada indicador: abrem a explicação daquele indicador
    document.addEventListener('click', e => {
      const a = e.target.closest('a[data-ind]');
      if (!a) return;
      indAlvo = a.dataset.ind;
      if (location.hash === '#como-calcular') { e.preventDefault(); rota(); }
    });
    $('copiarLink').addEventListener('click', () => WS.util.copiar(location.href, 'Link copiado'));
    tour = WS.tour.iniciar({ mapa, C, botao: $('abrirTour') });
    if (tourPedido) tour.abrir();
    window.addEventListener('hashchange', rota);
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { mapa.redesenhar(); if (analise) analise.graficos(); });
    rota();
    // Ganchos para o teste automático (testes/testar_front.py compara estes cálculos com a view SQL)
    window.PAINEL = { F: C.F, ANOS: C.ANOS, casos: C.casos, taxa: C.taxa, taxaEstado: C.taxaEstado, esperado: C.esperado, oe: C.oe,
      REG: C.REG, taxaRegiao: C.taxaRegiao, limitesMapa: mapa.limitesMapa, resumo: mapa.resumo, simbolos: mapa.simbolos, enquadramento: mapa.enquadramento, FX: C.FX, taxaFaixa: C.taxaFaixa, taxaFaixaEstado: C.taxaFaixaEstado, localEstado: C.localEstado, pctLocal: C.pctLocal,
      abrir: v => { location.hash = '#' + v; }, selecionar: cod => { location.hash = '#mapa-' + cod; },
      estado: mapa.S, imprimirFicha: mapa.imprimirFicha, abrirComparar: mapa.abrirComparar, origem };
  });
})();
