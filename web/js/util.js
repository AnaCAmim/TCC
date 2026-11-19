/* util.js: funções pequenas usadas por todos os módulos (formatação, DOM, copiar, baixar arquivo). */
"use strict";
window.WS = window.WS || {};
WS.util = (function () {
  const $ = id => document.getElementById(id);
  // número no formato brasileiro (1.234,5)
  const nf = (v, d = 0) => v == null || !isFinite(v) ? '–' : v.toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const semAc = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function toast(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.setAttribute('role', 'status'); t.textContent = msg;
    document.body.appendChild(t); setTimeout(() => t.remove(), 2200);
  }
  // copia texto para a área de transferência (com alternativa para navegadores sem a API)
  async function copiar(texto, msgOk) {
    try { await navigator.clipboard.writeText(texto); toast(msgOk || 'Copiado'); }
    catch (e) {
      const ta = document.createElement('textarea'); ta.value = texto; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
      ta.remove(); toast(ok ? (msgOk || 'Copiado') : 'Não foi possível copiar: selecione o endereço e use Ctrl+C');
    }
  }
  // oferece um arquivo para baixar (funciona com duplo clique e em servidor)
  function baixar(nome, conteudo, tipo) {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
    const a = document.createElement('a'); a.href = url; a.download = nome;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  // Barra única de 100% com legenda em número e % (a cor nunca é a única informação). itens: [{ rot, n, cor, k }]
  function barra100(itens) {
    const tot = itens.reduce((s, i) => s + i.n, 0), pct = n => (tot ? 100 * n / tot : 0);
    if (!tot) return '<p class="hint">Nenhuma notificação de 2019 a 2024.</p>';
    return '<div class="barra100" role="img" aria-label="' + esc(itens.map(i => i.rot + ': ' + nf(i.n) + ' (' + nf(pct(i.n), 1) + '%)').join('; ')) + '">' +
      itens.filter(i => i.n).map(i => '<span style="width:' + pct(i.n) + '%;background:' + i.cor + '"></span>').join('') + '</div>' +
      '<ul class="leg100">' + itens.map(i => '<li data-k="' + i.k + '"><span class="sw" style="background:' + i.cor + '"></span><span>' + i.rot + ': <b>' + nf(i.n) + '</b> ' +
        (i.n === 1 ? 'caso' : 'casos') + ' (<span class="pct">' + nf(pct(i.n), 1) + '%</span>)</span></li>').join('') + '</ul>';
  }
  return { $, nf, css, semAc, esc, toast, copiar, baixar, barra100 };
})();
