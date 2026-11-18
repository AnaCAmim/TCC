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
    const nomePer = per => (per === 'all' ? '2019 a 2024' : String(per));
    const rotFx = f => ({ '<1 Ano': 'Menos de 1', '60 e mais': '60 ou mais', 'Ign/Branco': 'Ignorada' }[f] || f.replace('-', ' a '));
    // Região de saúde: a MESMA taxa, somando casos e mulheres dos municípios da região (média da região na ficha)
    const REG = DADOS.regioes || {};
    const munsRegiao = reg => F.map(f => f.properties).filter(p => p.reg === reg);
    const casosRegiao = (reg, tipo, per) => munsRegiao(reg).reduce((s, p) => s + casos(p, tipo, per), 0);
    const popRegiao = reg => munsRegiao(reg).reduce((s, p) => s + p.pop, 0);
    const taxaRegiao = (reg, tipo, per) => casosRegiao(reg, tipo, per) / popRegiao(reg) * 1e5 / anosPer(per);
    const leituraOE = o => (!isFinite(o) ? '' : o < 0.8 ? 'Notifica menos que a média do estado' : o <= 1.25 ? 'Notifica perto da média do estado' : 'Notifica mais que a média do estado');
    return { F, ANOS, FX, POP, porCod, casos, anosPer, casosEstado, taxa, taxaEstado, esperado, oe, valor, faixaEstado, nomePer, rotFx, leituraOE, REG, munsRegiao, casosRegiao, popRegiao, taxaRegiao, TIPOS, NOME_IND };
  }

  // Tela "Como calcular": cada indicador com o que é, fórmula, exemplo com números reais, uso e cuidado
  function telaComoCalcular(C, el) {
    const { nf } = WS.util, ex = Object.values(C.porCod).find(p => p.nome === 'Sousa');
    const exc = C.casos(ex, 'total', 'all'), exe = C.esperado(ex, 'total', 'all'), tot = C.casosEstado('total', 'all'), fx = C.faixaEstado;
    const IND = [
      ['casos', 'Casos notificados', 'Quantas fichas de violência contra mulheres foram registradas no SINAN para mulheres que moram no município.',
        'Contagem direta do TABNET (SINAN), sexo feminino, por município de residência, excluída a violência autoprovocada.',
        ex.nome + ': ' + nf(exc) + ' casos de 2019 a 2024.', 'Mostra o volume de atendimento que a rede precisa absorver.',
        'Município grande tem mais casos só por ter mais gente. Para comparar municípios, use a taxa.'],
      ['taxa', 'Taxa por 100 mil mulheres por ano', 'Quantos casos houve por ano para cada 100 mil mulheres do município.',
        '<code class="f">casos ÷ mulheres × 100.000 ÷ número de anos</code>. As mulheres vêm do Censo 2022 (IBGE), o mesmo número para todos os anos.',
        ex.nome + ': ' + nf(exc) + ' ÷ ' + nf(ex.pop) + ' × 100.000 ÷ 6 = ' + nf(C.taxa(ex, 'total', 'all'), 1) + ' por 100 mil por ano. Estado: ' + nf(C.taxaEstado('total', 'all'), 1) + '.' +
          (C.REG[ex.reg] ? ' Média da região de saúde (' + C.REG[ex.reg].nome + '): a mesma conta, somando os casos e as mulheres dos ' + nf(C.munsRegiao(ex.reg).length) + ' municípios da região = ' + nf(C.taxaRegiao(ex.reg, 'total', 'all'), 1) + '.' : ''),
        'Permite comparar municípios de tamanhos diferentes.',
        'Com menos de 10 casos, um caso a mais muda muito a taxa. Em 6 anos somados a taxa seria 6 vezes maior: aqui ela é sempre dividida pelo número de anos.'],
      ['tipos', 'Tipos de violência', 'Separa as notificações em física, psicológica/moral e sexual.', 'Campos de tipo de violência da ficha do SINAN.',
        'Estado: física ' + nf(C.casosEstado('fisica', 'all')) + ', psicológica/moral ' + nf(C.casosEstado('psicologica', 'all')) + ', sexual ' + nf(C.casosEstado('sexual', 'all')) + '.',
        'Ajuda a decidir que tipo de serviço reforçar (por exemplo, atendimento à violência sexual).',
        'Uma mesma notificação pode marcar mais de um tipo. Por isso os tipos somados dão mais que o total.'],
      ['faixa', 'Faixa etária', 'Idade das mulheres e meninas nas notificações.', 'Contagem do TABNET por faixa etária, somando 2019 a 2024, para todos os tipos juntos.',
        'Estado: 20 a 29 anos tem ' + nf(fx[5]) + ' casos (' + nf(100 * fx[5] / tot, 1) + '%).',
        'Mostra qual público as políticas precisam alcançar (crianças, adolescentes, adultas, idosas).',
        'Aqui é contagem, não taxa: não há população feminina por idade de cada município nesta versão.'],
      ['oe', 'Observado ÷ esperado', 'Compara o município com o estado: quantas vezes ele notifica em relação ao que notificaria se seguisse a média estadual.',
        '<code class="f">esperado = mulheres do município × (casos do estado ÷ mulheres do estado)</code> e <code class="f">observado ÷ esperado = casos ÷ esperado</code>.',
        ex.nome + ': esperado ' + nf(exe, 1) + ' casos; observado ' + nf(exc) + '; ' + nf(exc) + ' ÷ ' + nf(exe, 1) + ' = ' + nf(exc / exe, 2) + '. Notificou cerca de ' + nf(100 * exc / exe, 0) + '% do que seria esperado.',
        '1 = igual ao estado; 0,5 = metade; 2 = o dobro. Bom para achar municípios muito fora da média.',
        'Notificar menos não quer dizer ter menos violência: pode ser dificuldade de acesso ou de registro. Em municípios com poucos casos o número oscila muito.']
    ];
    el.innerHTML = '<div class="card" style="margin:0"><h2>Os cinco indicadores deste painel</h2><p class="desc" style="margin:0">Todos vêm de duas fontes públicas: SINAN/TABNET (casos) e Censo 2022 do IBGE (número de mulheres). Nenhum modelo estatístico complexo é usado; as contas abaixo podem ser refeitas numa planilha.</p></div>' +
      IND.map(i => '<article id="ind-' + i[0] + '" tabindex="-1"><h2>' + i[1] + '</h2><dl><dt>O que é</dt><dd>' + i[2] + '</dd><dt>Como se calcula</dt><dd>' + i[3] +
        '</dd><dt>Exemplo</dt><dd>' + i[4] + '</dd><dt>Para que serve</dt><dd>' + i[5] + '</dd><dt>Cuidado</dt><dd>' + i[6] + '</dd></dl></article>').join('') +
      '<div class="card" style="margin:0"><h2>Fontes e limitações</h2><p class="desc" style="margin:0">Notificações: SINAN/TABNET (Ministério da Saúde), mulheres, município de residência, sem violência autoprovocada. Mulheres: Censo 2022 (IBGE, SIDRA 9514), o mesmo denominador em todos os anos. Regiões e macrorregiões de saúde: Base Territorial do Ministério da Saúde/DATASUS (junho de 2026). O SINAN de 2023 e 2024 ainda pode ser revisado. A notificação mede o registro, não a ocorrência.</p></div>';
  }
  return { criar, telaComoCalcular, TIPOS, NOME_IND };
})();
