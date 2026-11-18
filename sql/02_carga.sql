-- Carga dos dados brutos (executar com o diretório de trabalho em /websig, onde ficam dados/ e sql/).
-- Aborta (RAISE EXCEPTION + ON_ERROR_STOP) se algum total não bater: 223 municípios, 2.055.832 mulheres, 10.344 casos.
SET search_path = websig, public;

-- População feminina e nomes oficiais (IBGE)
CREATE TEMP TABLE st_pop (cod_ibge7 text, cod_ibge6 text, nome text, pop int);
\copy st_pop FROM 'dados/brutos/ibge_populacao_feminina_2022.csv' CSV HEADER

-- Malha municipal (GeoJSON); ST_MakeValid corrige a geometria inválida de Cabedelo
INSERT INTO municipio (cod_ibge7, cod_ibge6, nome, geom)
SELECT f->'properties'->>'id', left(f->'properties'->>'id', 6), p.nome,
       ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(f->>'geometry'), 4326)), 3))
FROM jsonb_array_elements(pg_read_file('/websig/dados/brutos/malha_municipal_pb_geojs.json')::jsonb->'features') AS f
JOIN st_pop p ON p.cod_ibge7 = f->'properties'->>'id';

INSERT INTO populacao SELECT cod_ibge7, pop FROM st_pop;

-- Notificações (TABNET, formato longo). 000000 = "município ignorado": precisa ter zero casos.
CREATE TEMP TABLE st_not (cod_ibge6 text, municipio text, ano int, tipo text, casos int);
\copy st_not FROM 'dados/brutos/sinan_pb_mulheres_residencia_2019-2024_longo.csv' CSV HEADER
DO $$ BEGIN
  IF (SELECT COALESCE(SUM(casos), 0) FROM st_not WHERE cod_ibge6 = '000000'
      AND tipo IN ('total_sem_autoprovocada', 'fisica', 'psicologica_moral', 'sexual')) <> 0 THEN
    RAISE EXCEPTION 'Há casos em "município ignorado": revisar a extração';
  END IF;
END $$;
INSERT INTO notificacao (cod_ibge6, ano, tipo, casos)
SELECT cod_ibge6, ano,
       CASE tipo WHEN 'total_sem_autoprovocada' THEN 'total' WHEN 'psicologica_moral' THEN 'psicologica' ELSE tipo END,
       casos
FROM st_not
WHERE cod_ibge6 <> '000000' AND tipo IN ('total_sem_autoprovocada', 'fisica', 'psicologica_moral', 'sexual');

-- Faixa etária (municípios sem nenhum caso não aparecem no TABNET: entram com zero)
CREATE TEMP TABLE st_fx (cod_ibge6 text, municipio text, faixa text, casos int);
\copy st_fx FROM 'dados/brutos/sinan_pb_mulheres_residencia_faixa_etaria_2019-2024.csv' CSV HEADER
CREATE TEMP TABLE ordem_faixa (faixa_id smallint, faixa text);
INSERT INTO ordem_faixa VALUES (1,'<1 Ano'),(2,'1-4'),(3,'5-9'),(4,'10-14'),(5,'15-19'),(6,'20-29'),
  (7,'30-39'),(8,'40-49'),(9,'50-59'),(10,'60 e mais'),(11,'Ign/Branco');
INSERT INTO faixa_etaria (cod_ibge6, faixa_id, faixa, casos)
SELECT m.cod_ibge6, o.faixa_id, o.faixa, COALESCE(s.casos, 0)
FROM municipio m CROSS JOIN ordem_faixa o
LEFT JOIN st_fx s ON s.cod_ibge6 = m.cod_ibge6 AND s.faixa = o.faixa;

-- Região de saúde (DATASUS, Base Territorial jun/2026; arquivos originais, Brasil inteiro, filtrados aqui para a PB)
CREATE TEMP TABLE st_mun_reg (co_municip text, co_regsaud text);
\copy st_mun_reg FROM 'dados/brutos/datasus_base_territorial_jun26/rl_municip_regsaud.csv' CSV HEADER DELIMITER ';'
CREATE TEMP TABLE st_reg (co_regsaud text, co_status text, ds_nome text, ds_nomepad text, ds_abrev text, nu_ordem text);
\copy st_reg FROM 'dados/brutos/datasus_base_territorial_jun26/tb_regsaud.txt' WITH (FORMAT text, HEADER true)
CREATE TEMP TABLE st_reg_mac (co_regsaud text, co_macsaud text);
\copy st_reg_mac FROM 'dados/brutos/datasus_base_territorial_jun26/rl_regsaud_macsaud.csv' CSV HEADER DELIMITER ';'
CREATE TEMP TABLE st_mac (co_macsaud text, co_status text, ds_nome text, ds_nomepad text, ds_abrev text, nu_ordem text);
\copy st_mac FROM 'dados/brutos/datasus_base_territorial_jun26/tb_macsaud.csv' CSV HEADER DELIMITER ';'
CREATE TEMP TABLE st_mun_mac (co_municip text, co_macsaud text);
\copy st_mun_mac FROM 'dados/brutos/datasus_base_territorial_jun26/rl_municip_macsaud.csv' CSV HEADER DELIMITER ';'
INSERT INTO regiao_saude (cod_ibge6, cod_regiao, regiao, cod_macro, macrorregiao)
SELECT m.cod_ibge6, r.co_regsaud, regexp_replace(r.ds_nome, '\s*-\s*PB$', ''),
       rm.co_macsaud, regexp_replace(mc.ds_abrev, '\s*-\s*PB$', '')
FROM municipio m
JOIN st_mun_reg mr ON mr.co_municip = m.cod_ibge6
JOIN st_reg r      ON r.co_regsaud = mr.co_regsaud AND r.co_status = 'S'
JOIN st_reg_mac rm ON rm.co_regsaud = r.co_regsaud
JOIN st_mac mc     ON mc.co_macsaud = rm.co_macsaud AND mc.co_status = 'S';

-- Conferências: param a carga se algo não bater
DO $$
DECLARE n int; p bigint; c bigint; fx bigint; linhas int; div int; n_mac int;
BEGIN
  SELECT count(*) INTO n FROM municipio;              IF n <> 223 THEN RAISE EXCEPTION 'municipios = % (esperado 223)', n; END IF;
  SELECT count(*), sum(pop_fem_2022) INTO linhas, p FROM populacao;
  IF linhas <> 223 OR p <> 2055832 THEN RAISE EXCEPTION 'populacao: % linhas, % mulheres (esperado 223 e 2055832)', linhas, p; END IF;
  SELECT sum(casos) INTO c FROM notificacao WHERE tipo = 'total';
  IF c <> 10344 THEN RAISE EXCEPTION 'casos = % (esperado 10344)', c; END IF;
  SELECT count(*) INTO linhas FROM notificacao;
  IF linhas <> 223 * 6 * 4 THEN RAISE EXCEPTION 'notificacao: % linhas (esperado %)', linhas, 223 * 6 * 4; END IF;
  SELECT sum(casos) INTO fx FROM faixa_etaria;
  IF fx <> 10344 THEN RAISE EXCEPTION 'faixa etaria soma % (esperado 10344)', fx; END IF;
  SELECT count(*) INTO div FROM (
    SELECT m.cod_ibge6 FROM municipio m
    WHERE (SELECT sum(casos) FROM notificacao WHERE cod_ibge6 = m.cod_ibge6 AND tipo = 'total')
       <> (SELECT sum(casos) FROM faixa_etaria WHERE cod_ibge6 = m.cod_ibge6)) x;
  IF div <> 0 THEN RAISE EXCEPTION '% municipios com faixa etaria diferente do total', div; END IF;
  SELECT count(*) INTO div FROM st_not WHERE cod_ibge6 <> '000000' AND cod_ibge6 NOT IN (SELECT cod_ibge6 FROM municipio);
  IF div <> 0 THEN RAISE EXCEPTION '% linhas do SINAN sem municipio correspondente', div; END IF;
  SELECT count(*), count(DISTINCT cod_regiao), count(DISTINCT cod_macro) INTO linhas, div, n_mac FROM regiao_saude;
  IF linhas <> 223 OR div <> 16 OR n_mac <> 3 THEN
    RAISE EXCEPTION 'regiao_saude: % municipios, % regioes, % macrorregioes (esperado 223, 16 e 3)', linhas, div, n_mac; END IF;
  SELECT count(*) INTO div FROM regiao_saude r JOIN st_mun_mac mm ON mm.co_municip = r.cod_ibge6 WHERE mm.co_macsaud <> r.cod_macro;
  IF div <> 0 THEN RAISE EXCEPTION '% municipios com macrorregiao diferente nas duas tabelas do DATASUS', div; END IF;
  SELECT count(*) INTO div FROM municipio WHERE NOT ST_IsValid(geom);
  IF div <> 0 THEN RAISE EXCEPTION '% geometrias invalidas', div; END IF;
  RAISE NOTICE 'Carga OK: % municipios, % casos, % mulheres, 16 regioes de saude', n, c, p;
END $$;
ANALYZE;
