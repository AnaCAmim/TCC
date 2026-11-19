-- WebSIG: painel de indicadores de violência contra a mulher na Paraíba (SINAN 2019-2024)
-- Esquema enxuto: só o necessário para os 5 indicadores (casos, taxa por 100 mil/ano, tipo, faixa etária, observado ÷ esperado).
SET client_min_messages = warning;   -- esconde avisos de rotina (extensão já existe, objetos removidos)
CREATE EXTENSION IF NOT EXISTS postgis;
DROP SCHEMA IF EXISTS websig CASCADE;
CREATE SCHEMA websig;
SET client_min_messages = notice;
SET search_path = websig, public;

-- Municípios da Paraíba com a geometria da malha municipal
CREATE TABLE municipio (
  cod_ibge7 char(7)     PRIMARY KEY,
  cod_ibge6 char(6)     NOT NULL UNIQUE,          -- código usado pelo SINAN/TABNET (7 dígitos sem o verificador)
  nome      varchar(80) NOT NULL,                 -- nome oficial (API de localidades do IBGE)
  geom      geometry(MultiPolygon, 4326) NOT NULL,
  CHECK (cod_ibge6 = left(cod_ibge7, 6))
);
CREATE INDEX municipio_geom_gix ON municipio USING GIST (geom);

-- Denominador: mulheres residentes, Censo 2022 (IBGE/SIDRA, tabela 9514), fixo para todos os anos
CREATE TABLE populacao (
  cod_ibge7    char(7) PRIMARY KEY REFERENCES municipio(cod_ibge7),
  pop_fem_2022 integer NOT NULL CHECK (pop_fem_2022 > 0)
);

-- Tipos de violência do painel (um caso pode ter mais de um tipo: os tipos NÃO somam o total)
CREATE TABLE tipo_violencia (
  codigo varchar(20) PRIMARY KEY,
  nome   varchar(60) NOT NULL,
  ordem  smallint    NOT NULL UNIQUE
);
INSERT INTO tipo_violencia VALUES
  ('total', 'Todos os tipos (sem violência autoprovocada)', 1),
  ('fisica', 'Física', 2),
  ('psicologica', 'Psicológica/moral', 3),
  ('sexual', 'Sexual', 4);

-- Notificações de mulheres por município de residência × ano × tipo (SINAN/TABNET)
CREATE TABLE notificacao (
  cod_ibge6 char(6)     NOT NULL REFERENCES municipio(cod_ibge6),
  ano       smallint    NOT NULL CHECK (ano BETWEEN 2019 AND 2024),
  tipo      varchar(20) NOT NULL REFERENCES tipo_violencia(codigo),
  casos     integer     NOT NULL CHECK (casos >= 0),
  PRIMARY KEY (cod_ibge6, ano, tipo)
);

-- Notificações (todos os tipos) por município × faixa etária, acumulado 2019-2024 (contagem, não taxa)
CREATE TABLE faixa_etaria (
  cod_ibge6 char(6)     NOT NULL REFERENCES municipio(cod_ibge6),
  faixa_id  smallint    NOT NULL CHECK (faixa_id BETWEEN 1 AND 11),
  faixa     varchar(20) NOT NULL,
  casos     integer     NOT NULL CHECK (casos >= 0),
  PRIMARY KEY (cod_ibge6, faixa_id)
);

-- Região de saúde e macrorregião de saúde de cada município (Ministério da Saúde/DATASUS, Base Territorial).
-- Só agrupa municípios: não muda nenhum caso nem fórmula. A Paraíba tem 16 regiões e 3 macrorregiões.
CREATE TABLE regiao_saude (
  cod_ibge6    char(6)     PRIMARY KEY REFERENCES municipio(cod_ibge6),
  cod_regiao   char(5)     NOT NULL,                 -- CO_REGSAUD (ex.: 25001)
  regiao       varchar(60) NOT NULL,                 -- nome oficial sem o " - PB" (ex.: "1ª Região Mata Atlântica")
  cod_macro    char(4)     NOT NULL,                 -- CO_MACSAUD (ex.: 2503)
  macrorregiao varchar(60) NOT NULL                  -- ex.: "Macrorregião I - João Pessoa"
);
CREATE INDEX regiao_saude_regiao_idx ON regiao_saude (cod_regiao);

-- Mulheres por faixa etária (Censo 2022, SIDRA 9514), nas MESMAS 10 faixas do SINAN (sem a "Ignorada").
-- Denominador da taxa por faixa: casos da faixa ÷ mulheres da faixa × 100.000 ÷ 6.
CREATE TABLE populacao_faixa (
  cod_ibge7 char(7)     NOT NULL REFERENCES municipio(cod_ibge7),
  faixa_id  smallint    NOT NULL CHECK (faixa_id BETWEEN 1 AND 10),
  faixa     varchar(20) NOT NULL,
  mulheres  integer     NOT NULL CHECK (mulheres >= 0),
  PRIMARY KEY (cod_ibge7, faixa_id)
);

-- Serviços declarados pela prefeitura na MUNIC 2023 (IBGE). Só contexto: não entra em nenhuma conta.
-- Valores exatamente como na MUNIC: 'Sim', 'Não' ou '-' (sem dado).
CREATE TABLE rede_atendimento (
  cod_ibge7                    char(7)    PRIMARY KEY REFERENCES municipio(cod_ibge7),
  organismo_politicas_mulheres varchar(3) NOT NULL CHECK (organismo_politicas_mulheres IN ('Sim', 'Não', '-')),  -- MPPM01
  centro_referencia            varchar(3) NOT NULL CHECK (centro_referencia IN ('Sim', 'Não', '-')),             -- MPPM24a1 (CEAM/NIAM)
  casa_abrigo                  varchar(3) NOT NULL CHECK (casa_abrigo IN ('Sim', 'Não', '-')),                   -- MPPM20
  delegacia_mulher             varchar(3) NOT NULL CHECK (delegacia_mulher IN ('Sim', 'Não', '-'))               -- MSEG168
);
