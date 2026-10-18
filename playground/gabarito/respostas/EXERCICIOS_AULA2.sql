-- Solucoes reservadas ao professor - Aula 2 (diagnostico e tratamento)
-- Rode com:
--   docker compose exec -T -e PGPASSWORD=ons_lab destino psql -U ons_lab -d analytics

-- 1) Resuma os defeitos detectados por tipo.
SELECT tipo, count(*) FROM aula2.diagnostico_duplicatas GROUP BY 1 ORDER BY 1;

-- 2) Liste as categorias (codigo/nome) fora do padrao e a forma canonica.
SELECT fonte, campo, valor_bruto, n, valor_canonico
FROM aula2.diagnostico_categorias ORDER BY fonte, campo;

-- 3) Onde estao as horas faltantes e quantas sao?
SELECT fonte, id_subsistema, horas_faltantes, horas_faltantes_lista
FROM aula2.diagnostico_lacunas WHERE horas_faltantes > 0;

-- 4) Quais valores extremos foram detectados? Distinga os que vao para a
--    quarentena DIDATICA (criterio de mediana/negativo, nao prova de
--    impossibilidade fisica) dos que apenas merecem revisao (IQR).
SELECT fonte, coluna, id_subsistema, din_instante, valor, criticidade, regra
FROM aula2.diagnostico_extremos ORDER BY fonte, coluna, din_instante;

-- 5) O que foi para a quarentena e por que?
SELECT motivo, count(*) FROM aula2.quarentena GROUP BY 1 ORDER BY 1;

-- 6) Exercicio de politica: mude aluno/parametros_aula2.json (mult_iqr=3),
--    rode 04 de novo e compare quantos extremos aparecem.
--    Depois volte ao valor 8 e justifique.

-- 7) Impacto das transformacoes: compare pico/cobertura de SE val_carga.
SELECT cenario, cobertura, media, pico
FROM aula2.avaliacao_indicadores
WHERE fonte = 'balanco' AND id_subsistema = 'SE' AND coluna = 'val_carga'
ORDER BY cenario;

-- 8) DESAFIO: quais linhas foram padronizadas (id ou nome)? Conte por flag.
SELECT count(*) FILTER (WHERE flags LIKE '%padronizacao_id%') AS id_padronizado,
       count(*) FILTER (WHERE flags LIKE '%padronizacao_nome%') AS nome_padronizado,
       count(*) FILTER (WHERE flags LIKE '%formato_numero_convertido%') AS numero_convertido
FROM aula2.limpo_balanco;
