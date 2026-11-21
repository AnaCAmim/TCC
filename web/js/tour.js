/* tour.js: roteiro guiado de 6 passos para a demonstração (Anterior/Próximo, setas ← → e Esc). */
"use strict";
window.WS = window.WS || {};
WS.tour = (function () {
  const { $ } = WS.util;
  function iniciar({ mapa, C, botao }) {
    const sousa = Object.values(C.porCod).find(p => p.nome === 'Sousa');
    const irMapa = () => { if (location.hash !== '#mapa') location.hash = '#mapa'; };
    const PASSOS = [
      { t: 'Mapa da taxa', x: 'Cor de cada município: taxa de notificação por 100 mil mulheres por ano. Tons mais escuros indicam taxas maiores.',
        ir: () => { irMapa(); mapa.definir('reg', ''); mapa.definir('tipo', 'total'); mapa.definir('per', 'all'); mapa.definir('ind', 'taxa'); } },
      { t: 'Observado ÷ esperado', x: 'Cada município comparado com o estado. Azul: abaixo do esperado. Vermelho: acima. O ranking "10 menores" lista os valores mais baixos entre os municípios com pelo menos 10 casos.',
        ir: () => { irMapa(); mapa.definir('ind', 'oe'); } },
      { t: 'Ficha de ' + sousa.nome, x: 'A ficha abre com uma frase-resumo. Em seguida vêm os 5 indicadores comparados com o estado e, depois, os contextos.',
        ir: () => { mapa.definir('ind', 'oe'); location.hash = '#mapa-' + sousa.cod; } },
      { t: 'Faixa etária em taxa', x: 'A taxa por 100 mil mulheres da faixa permite comparar idades com populações diferentes. O traço marca o estado.',
        ir: () => { if (location.hash !== '#mapa-' + sousa.cod) location.hash = '#mapa-' + sousa.cod; setTimeout(mapa.verFaixaTaxa, 450); } },
      { t: 'Análise', x: 'Principais resultados do estado, calculados dos dados. Cada um traz uma pergunta para a gestão.',
        ir: () => { location.hash = '#analise'; setTimeout(() => { const s = $('v-analise').querySelector('.scroll'); if (s) s.scrollTop = 0; }, 80); } },
      { t: 'Como calcular', x: 'Fórmula e exemplo de cada indicador. Todas as contas podem ser refeitas numa planilha.',
        ir: () => { location.hash = '#como-calcular'; } }
    ];
    let i = -1;
    const el = $('tour');
    function mostrar(n) {
      i = Math.max(0, Math.min(PASSOS.length - 1, n));
      const p = PASSOS[i];
      $('tourPasso').textContent = 'Passo ' + (i + 1) + ' de ' + PASSOS.length;
      $('tourT').textContent = p.t; $('tourTxt').textContent = p.x;
      $('tourAnt').disabled = i === 0;
      $('tourProx').textContent = i === PASSOS.length - 1 ? 'Concluir' : 'Próximo';
      p.ir();
    }
    function abrir() { el.hidden = false; mostrar(0); $('tourT').focus(); }
    function fechar() { el.hidden = true; i = -1; botao.focus(); }
    $('tourAnt').addEventListener('click', () => mostrar(i - 1));
    $('tourProx').addEventListener('click', () => (i === PASSOS.length - 1 ? fechar() : mostrar(i + 1)));
    $('tourSair').addEventListener('click', fechar);
    // teclas: valem com o tour aberto, fora de campos de texto e listas (captura: roda antes do Esc da ficha)
    document.addEventListener('keydown', e => {
      if (el.hidden || e.target.closest('input,select,textarea')) return;
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); fechar(); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); e.stopPropagation(); mostrar(i + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); mostrar(i - 1); }
    }, true);
    return { abrir, fechar, passo: () => i, total: PASSOS.length };
  }
  return { iniciar };
})();
