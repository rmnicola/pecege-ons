-- Solucoes reservadas ao professor - Aula 1 (destino "analytics")
-- Rode com:
--   docker compose exec -T -e PGPASSWORD=ons_lab destino psql -U ons_lab -d analytics
-- ou, dentro do container etl: psql -h destino -U ons_lab -d analytics

-- 1) Quantas linhas foram integradas? Quantas sao de subsistemas fisicos e
--    quantas sao do agregado SIN?
--    (esperado: 840 / 672 / 168)
-- TODO aluno:
SELECT tipo_subsistema, count(*) FROM aula1.integrado GROUP BY 1 ORDER BY 1;

-- 2) A chave (id_subsistema, din_instante) e unica? Escreva uma consulta que
--    retorne 0 linhas se for unica.
-- TODO aluno:
SELECT id_subsistema, din_instante, count(*)
FROM aula1.integrado
GROUP BY 1, 2 HAVING count(*) > 1;

-- 3) Em quantas linhas as duas medidas de carga divergem?
--    (esperado: 0 no recorte de 2025; explique que isso foi verificado)
SELECT count(*) AS divergentes
FROM aula1.integrado
WHERE tem_curva AND NOT carga_coincide;

-- 4) Qual o pico de carga por subsistema em cada base?
SELECT id_subsistema,
       max(val_carga) AS pico_balanco,
       max(val_cargaenergiahomwmed) AS pico_curva
FROM aula1.integrado
WHERE tipo_subsistema = 'subsistema'
GROUP BY 1 ORDER BY 1;

-- 5) Confira a rastreabilidade: de quais servicos/tabelas cada medida veio?
SELECT DISTINCT _fonte_servico, _tabela_origem, _sha256_recorte
FROM aula1.stg_balanco;

-- 6) DESAFIO: o SIN e igual a soma dos subsistemas? Calcule o residuo maximo.
--    Lembre: isso e diagnostico, nao um erro automatico.
SELECT max(abs(sin.val_carga - s.soma)) AS residuo_max
FROM aula1.integrado sin
JOIN (
  SELECT din_instante, sum(val_carga) AS soma
  FROM aula1.integrado WHERE tipo_subsistema = 'subsistema'
  GROUP BY din_instante
) s ON s.din_instante = sin.din_instante
WHERE sin.tipo_subsistema = 'agregado_sin';
