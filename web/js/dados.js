/* js/dados.js: carrega os dados do painel.
   Em servidor (http/https) lê dados.json; aberto com duplo clique (file://) usa o dados.js de reserva,
   que define window.DADOS. Os dois arquivos são gerados por pipeline/exportar.py a partir das views SQL. */
"use strict";
window.WS = window.WS || {};
WS.dados = (function () {
  function carregar(pronto) {
    // Erro com mensagem útil: o que aconteceu e o que fazer
    const falha = () => {
      const c = document.getElementById('carregando');
      if (c) c.remove();
      document.getElementById('conteudo').insertAdjacentHTML('afterbegin', '<div class="erro" role="alert"><h2>Não foi possível carregar os dados do painel</h2>' +
        '<p>Os arquivos <code>dados.json</code> e <code>dados.js</code> não foram encontrados ou estão danificados.</p>' +
        '<ul><li>Confira se eles estão na mesma pasta que <code>index.html</code>.</li><li>Se você baixou o painel, extraia o arquivo .zip inteiro antes de abrir.</li>' +
        '<li>Para gerar os dados de novo, rode <code>atualizar.bat</code>.</li></ul><p><button class="btn pri" type="button" onclick="location.reload()">Tentar de novo</button></p></div>');
    };
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
