-- Carga do banco na primeira subida do contêiner (docker-entrypoint-initdb.d).

-- Recorte de 01 a 07/01/2025 da Curva de Carga Horária do ONS, sem alterações.
CREATE SCHEMA oficial;
CREATE TABLE oficial.curva_horaria (
    id_subsistema text NOT NULL,
    nom_subsistema text,
    din_instante timestamp NOT NULL,
    val_cargaenergiahomwmed numeric,
    PRIMARY KEY (id_subsistema, din_instante)
);
COPY oficial.curva_horaria FROM '/docker-entrypoint-initdb.d/curva_oficial.csv'
    WITH (FORMAT csv, DELIMITER ';', HEADER);

-- Aula 2: cópia didática do mesmo recorte, toda em texto, com cinco tipos de falha
-- inseridos de propósito. Não são defeitos da base do ONS (lista em .lab/gabarito/aula2/defeitos.md).
CREATE SCHEMA laboratorio;
CREATE TABLE laboratorio.curva_horaria (
    id_subsistema text,
    nom_subsistema text,
    din_instante text,
    val_cargaenergiahomwmed text
);
COPY laboratorio.curva_horaria FROM '/docker-entrypoint-initdb.d/curva_laboratorio.csv'
    WITH (FORMAT csv, DELIMITER ';', HEADER,
          FORCE_NOT_NULL (id_subsistema, nom_subsistema, din_instante, val_cargaenergiahomwmed));

-- De onde veio o recorte.
CREATE SCHEMA meta;
CREATE TABLE meta.proveniencia AS SELECT
    'curva'::text AS fonte,
    'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/curva-carga-ho/CURVA_CARGA_2025.csv'::text AS url,
    '69a3d2560bf111e46d1fa356ee4be7c917ca89bf53ae16ab1af9f9e7477ff4c4'::text AS sha256_arquivo_origem,
    '2025-01-01 00:00:00'::timestamp AS recorte_inicio,
    '2025-01-08 00:00:00'::timestamp AS recorte_fim,
    '2026-10-13 15:12:35+00'::timestamptz AS extraido_em;
