/* calculo.js: as fórmulas dos 5 indicadores (as MESMAS das views SQL) e a tela "Como calcular".
   taxa por 100 mil mulheres por ano = casos ÷ mulheres × 100.000 ÷ número de anos
   esperado = mulheres do município × (casos do estado ÷ mulheres do estado)   (mesmo tipo e período)
   observado ÷ esperado = casos ÷ esperado */
"use strict";
window.WS = window.WS || {};
WS.calculo = (function () {
  const TIPOS = { total: 'Todos os tipos', fisica: 'Física', psicologica: 'Psicológica/moral', sexual: 'Sexual' };
  const NOME_IND = { casos: 'Casos notificados', taxa: 'Taxa por 100 mil mulheres por ano', oe: 'Observado ÷ esperado' };

  function criar(DADOS) {
    const F = DADOS.features, ANOS = DADOS.anos, FX = DADOS.faixas;
    const POP = F.reduce((s, f) => s + f.properties.pop, 0);
    const porCod = {}; F.forEach(f => { porCod[f.properties.cod] = f.properties; });
    // casos de um município num período: soma dos 6 anos ('all') ou um ano só
    const casos = (p, tipo, per) => { const v = p.casos[tipo]; return per === 'all' ? v.reduce((a, b) => a + b, 0) : v[ANOS.indexOf(+per)]; };
    const anosPer = per => (per === 'all' ? ANOS.length : 1);
    const casosEstado = (tipo, per) => F.reduce((s, f) => s + casos(f.properties, tipo, per), 0);
    const taxa = (p, tipo, per) => casos(p, tipo, per) / p.pop * 1e5 / anosPer(per);
    const taxaEstado = (tipo, per) => casosEstado(tipo, per) / POP * 1e5 / anosPer(per);
    const esperado = (p, tipo, per) => p.pop * casosEstado(tipo, per) / POP;
    const oe = (p, tipo, per) => casos(p, tipo, per) / esperado(p, tipo, per);
    const valor = (p, ind, tipo, per) => (ind === 'casos' ? casos(p, tipo, per) : ind === 'taxa' ? taxa(p, tipo, per) : oe(p, tipo, per));
    const faixaEstado = FX.map((_, i) => F.reduce((s, f) => s + f.properties.faixa[i], 0));
    // Taxa por faixa etária = casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6 (as 10 faixas do SINAN; a "Ignorada" não tem taxa)
    const N_FX_TAXA = 10;
    const popFaixaEstado = FX.slice(0, N_FX_TAXA).map((_, i) => F.reduce((s, f) => s + f.properties.popfx[i], 0));
    const taxaFaixa = (p, i) => (i < N_FX_TAXA && p.popfx[i] > 0 ? p.faixa[i] / p.popfx[i] * 1e5 / ANOS.length : null);
    const taxaFaixaEstado = i => (i < N_FX_TAXA ? faixaEstado[i] / popFaixaEstado[i] * 1e5 / ANOS.length : null);
    const nomePer = per => (per === 'all' ? '2019 a 2024' : String(per));
    const rotFx = f => ({ '<1 Ano': 'Menos de 1', '60 e mais': '60 ou mais', 'Ign/Branco': 'Ignorada' }[f] || f.replace('-', ' a '));
    // Região de saúde: a MESMA taxa, somando casos e mulheres dos municípios da região (média da região na ficha)
    const REG = DADOS.regioes || {};
    const munsRegiao = reg => F.map(f => f.properties).filter(p => p.reg === reg);
    const casosRegiao = (reg, tipo, per) => munsRegiao(reg).reduce((s, p) => s + casos(p, tipo, per), 0);
    const popRegiao = reg => munsRegiao(reg).reduce((s, p) => s + p.pop, 0);
    const taxaRegiao = (reg, tipo, per) => casosRegiao(reg, tipo, per) / popRegiao(reg) * 1e5 / anosPer(per);
    // Local de notificação (contexto): [mesma região de saúde, outra região da PB, fora da Paraíba]; % = casos na categoria ÷ casos do município × 100
    const LOCAIS = ['Mesma região de saúde', 'Outra região da Paraíba', 'Fora da Paraíba'];
    const localEstado = [0, 1, 2].map(k => F.reduce((s, f) => s + f.properties.local[k], 0));
    const pctLocal = (vals, k) => { const t = vals[0] + vals[1] + vals[2]; return t ? 100 * vals[k] / t : null; };
    const leituraOE = o => (!isFinite(o) ? '' : o < 0.8 ? 'Notifica menos que a média do estado' : o <= 1.25 ? 'Notifica perto da média do estado' : 'Notifica mais que a média do estado');
    const CONTORNOS = DADOS.contornos || null;   // estado e regiões de saúde, só para desenho do mapa
    return { CONTORNOS, F, ANOS, FX, POP, porCod, casos, anosPer, casosEstado, taxa, taxaEstado, esperado, oe, valor, faixaEstado, popFaixaEstado, taxaFaixa, taxaFaixaEstado, N_FX_TAXA, nomePer, rotFx, leituraOE, LOCAIS, localEstado, pctLocal, REG, munsRegiao, casosRegiao, popRegiao, taxaRegiao, TIPOS, NOME_IND };
  }

  // Tela "Como calcular": cada indicador com o que é, fórmula, exemplo com números reais, uso e cuidado
  function telaComoCalcular(C, el) {
    const { nf } = WS.util, ex = Object.values(C.porCod).find(p => p.nome === 'Sousa');
    const exc = C.casos(ex, 'total', 'all'), exe = C.esperado(ex, 'total', 'all'), tot = C.casosEstado('total', 'all'), fx = C.faixaEstado;
    const cg = Object.values(C.porCod).find(p => p.nome === 'Campina Grande');
    const IND = [
      ['casos', 'Casos notificados', 'Fichas de notificação do SINAN de mulheres residentes no município.',
        'Contagem do TABNET: sexo feminino, município de residência, sem violência autoprovocada.',
        ex.nome + ': ' + nf(exc) + ' casos de 2019 a 2024.', 'Volume de atendimento da rede.',
        'Depende do tamanho do município. Para comparar municípios, use a taxa.'],
      ['taxa', 'Taxa por 100 mil mulheres por ano', 'Casos por ano a cada 100 mil mulheres do município.',
        '<code class="f">casos ÷ mulheres × 100.000 ÷ número de anos</code>. Mulheres: Censo 2022 (IBGE), o mesmo número em todos os anos.',
        ex.nome + ': ' + nf(exc) + ' ÷ ' + nf(ex.pop) + ' × 100.000 ÷ 6 = ' + nf(C.taxa(ex, 'total', 'all'), 1) + ' por 100 mil por ano. Estado: ' + nf(C.taxaEstado('total', 'all'), 1) + '.' +
          (C.REG[ex.reg] ? ' Média da ' + C.REG[ex.reg].nome + ' de saúde: a mesma conta com os casos e as mulheres dos ' + nf(C.munsRegiao(ex.reg).length) + ' municípios da região, ' + nf(C.taxaRegiao(ex.reg, 'total', 'all'), 1) + '.' : ''),
        'Comparar municípios de tamanhos diferentes.',
        'No período 2019 a 2024, a soma dos casos é dividida por 6 para manter a taxa anual.'],
      ['tipos', 'Tipos de violência', 'Notificações por tipo: física, psicológica/moral e sexual.', 'Campos de tipo de violência da ficha do SINAN.',
        'Estado: física ' + nf(C.casosEstado('fisica', 'all')) + '; psicológica/moral ' + nf(C.casosEstado('psicologica', 'all')) + '; sexual ' + nf(C.casosEstado('sexual', 'all')) + '.',
        'Indicar que tipo de serviço reforçar.',
        'Uma notificação pode ter mais de um tipo. A soma dos tipos passa do total.'],
      ['faixa', 'Faixa etária', 'Idade das mulheres e meninas notificadas, em casos ou em taxa.',
        'Casos: contagem do TABNET por faixa, 2019 a 2024, todos os tipos. Taxa: <code class="f">casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6</code>. Mulheres por faixa: Censo 2022 (SIDRA 9514), com os grupos de idade do IBGE somados nas faixas do SINAN.',
        'Estado, 10 a 14 anos: ' + nf(fx[3]) + ' ÷ ' + nf(C.popFaixaEstado[3]) + ' × 100.000 ÷ 6 = ' + nf(C.taxaFaixaEstado(3), 1) + ' por 100 mil por ano, a maior taxa entre as faixas. 20 a 29 anos tem mais casos (' + nf(fx[5]) + ') e taxa de ' + nf(C.taxaFaixaEstado(5), 1) + '. ' +
          (cg ? cg.nome + ', 20 a 29 anos: ' + nf(cg.faixa[5]) + ' ÷ ' + nf(cg.popfx[5]) + ' × 100.000 ÷ 6 = ' + nf(C.taxaFaixa(cg, 5), 1) + '.' : ''),
        'Indicar o público a alcançar.',
        'As faixas têm larguras diferentes (5 ou 10 anos); para compará-las, use a taxa. A faixa "Ignorada" não tem taxa.'],
      ['oe', 'Observado ÷ esperado', 'Compara o município com o estado.',
        '<code class="f">esperado = mulheres do município × (casos do estado ÷ mulheres do estado)</code> e <code class="f">observado ÷ esperado = casos ÷ esperado</code>.',
        ex.nome + ': esperado ' + nf(exe, 1) + ' casos; observado ' + nf(exc) + '; ' + nf(exc) + ' ÷ ' + nf(exe, 1) + ' = ' + nf(exc / exe, 2) + ', ou ' + nf(100 * exc / exe, 0) + '% do esperado.',
        '1 = igual ao estado; 0,5 = metade; 2 = o dobro.',
        'Notificar menos pode indicar dificuldade de acesso ou de registro, e não menos violência.']
    ];
    const exl = ex.local, exT = exl[0] + exl[1] + exl[2], el3 = C.localEstado, elT = el3[0] + el3[1] + el3[2];
    const contexto = '<article id="ctx-local" tabindex="-1"><h2>Contexto: local de atendimento</h2><dl><dt>O que é</dt><dd>Onde as notificações das mulheres do município foram feitas: na mesma região de saúde, em outra região da Paraíba ou fora do estado. Não é um indicador.</dd>' +
      '<dt>Como se calcula</dt><dd><code class="f">casos atendidos na categoria ÷ casos do município × 100</code>. Regiões de notificação: TABNET (SINAN). Fora da Paraíba = casos por residência − casos notificados na Paraíba (o TABNET só lista municípios de notificação da Paraíba).</dd>' +
      '<dt>Exemplo</dt><dd>' + ex.nome + ': ' + nf(exl[0]) + ' ÷ ' + nf(exT) + ' × 100 = ' + nf(C.pctLocal(exl, 0), 1) + '% na própria região de saúde. Estado: ' + nf(el3[0]) + ' ÷ ' + nf(elT) + ' × 100 = ' + nf(C.pctLocal(el3, 0), 1) + '%; ' + nf(el3[2]) + ' casos (' + nf(C.pctLocal(el3, 2), 1) + '%) fora da Paraíba.</dd>' +
      '<dt>Cuidado</dt><dd>O dado não informa o motivo do atendimento em outra região.</dd></dl></article>';
    el.innerHTML = '<div class="card" style="border-top:0"><h2>Como os indicadores são calculados</h2><p class="desc" style="margin:0">Fontes: SINAN/TABNET (casos) e Censo 2022, IBGE (mulheres). Todas as contas podem ser refeitas numa planilha.</p></div>' +
      IND.map(i => '<article id="ind-' + i[0] + '" tabindex="-1"><h2>' + i[1] + '</h2><dl><dt>O que é</dt><dd>' + i[2] + '</dd><dt>Como se calcula</dt><dd>' + i[3] +
        '</dd><dt>Exemplo</dt><dd>' + i[4] + '</dd><dt>Para que serve</dt><dd>' + i[5] + '</dd><dt>Cuidado</dt><dd>' + i[6] + '</dd></dl></article>').join('') + contexto +
      '<div class="card"><h2>Fontes e limitações</h2><p class="desc" style="margin:0">Notificações e local de notificação: SINAN/TABNET (Ministério da Saúde), mulheres, município de residência, sem violência autoprovocada. Mulheres, total e por faixa etária: Censo 2022 (IBGE, SIDRA 9514), o mesmo denominador em todos os anos. Serviços declarados: MUNIC 2023 (IBGE). Regiões de saúde: Base Territorial do DATASUS (junho de 2026). Os dados de 2023 e 2024 do SINAN ainda podem ser revisados.</p></div>';
  }
  return { criar, telaComoCalcular, TIPOS, NOME_IND };
})();
