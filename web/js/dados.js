/* js/dados.js: carrega os dados do painel.
   Em servidor (http/https) lê dados.json; aberto com duplo clique (file://) usa o dados.js de reserva,
   que define window.DADOS. Os dois arquivos são gerados por pipeline/exportar.py a partir das views SQL. */
"use strict";
window.WS = window.WS || {};
WS.dados = (function () {
  function carregar(pronto) {
    const falha = () => document.body.insertAdjacentHTML('afterbegin',
      '<p role="alert" style="padding:16px;background:#fde7e4;color:#7a1c12;margin:0">Não foi possível carregar os dados do painel (dados.json ou dados.js).</p>');
    const viaScript = () => {
      const s = document.createElement('script');
      s.src = 'dados.js';
      s.onload = () => (window.DADOS ? pronto(window.DADOS, 'dados.js') : falha());
      s.onerror = falha;
      document.head.appendChild(s);
    };
    if (location.protocol.startsWith('http')) {
      fetch('dados.json', { cache: 'no-cache' })
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(d => pronto(d, 'dados.json'))
        .catch(viaScript);
    } else viaScript();
  }
  return { carregar };
})();
