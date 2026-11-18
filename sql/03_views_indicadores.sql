-- Views dos indicadores. O cálculo mora aqui; o painel repete as MESMAS fórmulas (tela "Como calcular"):
--   taxa por 100 mil mulheres por ano = casos ÷ mulheres × 100.000 ÷ número de anos
--   esperado = mulheres do município × (casos do estado ÷ mulheres do estado)   (mesmo tipo e mesmo período)
--   observado ÷ esperado = casos ÷ esperado
-- Período: cada ano (número de anos = 1) ou o acumulado 2019-2024 (número de anos = 6).
SET search_path = websig, public;

-- Casos por município, tipo e período (anos isolados + acumulado)
CREATE OR REPLACE VIEW vw_casos_periodo AS
SELECT cod_ibge6, ano::text AS periodo, ano, 1 AS n_anos, tipo, casos
FROM notificacao
UNION ALL
SELECT cod_ibge6, '2019-2024', NULL::smallint, 6, tipo, SUM(casos)::integer
FROM notificacao
GROUP BY cod_ibge6, tipo;

-- Estado (Paraíba): referência para o esperado e para a legenda do mapa
CREATE OR REPLACE VIEW vw_indicador_estado AS
SELECT c.periodo, c.ano, c.n_anos, c.tipo,
       SUM(c.casos)::integer AS casos,
       pe.pop_fem_2022,
       SUM(c.casos)::numeric / pe.pop_fem_2022 * 100000 / c.n_anos AS taxa_100mil_ano
FROM vw_casos_periodo c
CROSS JOIN (SELECT SUM(pop_fem_2022)::integer AS pop_fem_2022 FROM populacao) pe
GROUP BY c.periodo, c.ano, c.n_anos, c.tipo, pe.pop_fem_2022;

-- Município × período × tipo
CREATE OR REPLACE VIEW vw_indicador_municipio_ano_tipo AS
SELECT m.cod_ibge7, m.cod_ibge6, m.nome,
       c.periodo, c.ano, c.n_anos, c.tipo,
       c.casos,
       p.pop_fem_2022,
       c.casos::numeric / p.pop_fem_2022 * 100000 / c.n_anos                              AS taxa_100mil_ano,
       p.pop_fem_2022 * e.casos::numeric / e.pop_fem_2022                                 AS esperado,
       c.casos::numeric / NULLIF(p.pop_fem_2022 * e.casos::numeric / e.pop_fem_2022, 0)   AS o_sobre_e
FROM vw_casos_periodo c
JOIN municipio m ON m.cod_ibge6 = c.cod_ibge6
JOIN populacao p ON p.cod_ibge7 = m.cod_ibge7
JOIN vw_indicador_estado e ON e.periodo = c.periodo AND e.tipo = c.tipo;

-- Região de saúde × período × tipo: a MESMA taxa, somando casos e mulheres dos municípios da região
-- (usada na ficha como "média da região", ao lado da média do estado)
CREATE OR REPLACE VIEW vw_indicador_regiao AS
SELECT r.cod_regiao, r.regiao, r.macrorregiao, c.periodo, c.ano, c.n_anos, c.tipo,
       SUM(c.casos)::integer        AS casos,
       SUM(p.pop_fem_2022)::integer AS pop_fem_2022,
       SUM(c.casos)::numeric / SUM(p.pop_fem_2022) * 100000 / c.n_anos AS taxa_100mil_ano
FROM vw_casos_periodo c
JOIN regiao_saude r ON r.cod_ibge6 = c.cod_ibge6
JOIN municipio m    ON m.cod_ibge6 = c.cod_ibge6
JOIN populacao p    ON p.cod_ibge7 = m.cod_ibge7
GROUP BY r.cod_regiao, r.regiao, r.macrorregiao, c.periodo, c.ano, c.n_anos, c.tipo;

-- Conferência das views
DO $$
DECLARE c bigint; n int;
BEGIN
  SELECT casos INTO c FROM vw_indicador_estado WHERE periodo = '2019-2024' AND tipo = 'total';
  IF c <> 10344 THEN RAISE EXCEPTION 'vw_indicador_estado: % casos (esperado 10344)', c; END IF;
  SELECT count(*) INTO n FROM vw_indicador_municipio_ano_tipo WHERE periodo = '2019-2024' AND tipo = 'total';
  IF n <> 223 THEN RAISE EXCEPTION 'vw_indicador_municipio_ano_tipo: % municipios (esperado 223)', n; END IF;
  SELECT sum(casos) INTO c FROM vw_indicador_regiao WHERE periodo = '2019-2024' AND tipo = 'total';
  IF c <> 10344 THEN RAISE EXCEPTION 'vw_indicador_regiao: % casos (esperado 10344)', c; END IF;
  RAISE NOTICE 'Views OK: % casos, % municipios', c, n;
END $$;
