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
  return { $, nf, css, semAc, esc, toast, copiar, baixar };
})();
