-- Aula 1: escreva consultas no banco analytics (servico destino).
-- Antes da integracao, use aula1.stg_balanco e aula1.stg_curva.
-- Depois da integracao, use aula1.integrado.

-- 1. Inspecione tipos e colunas das duas tabelas de staging.
-- TODO: consulta

-- 2. Determine a granularidade e teste a unicidade da chave proposta.
-- Sua consulta deve listar apenas chaves que aparecem mais de uma vez.
-- TODO: consulta

-- 3. Compare grupos e periodos cobertos por cada fonte.
-- Distinga cobertura esperada de ausencia inesperada pelos dicionarios.
-- TODO: consulta

-- 4. Apos integrar, confira linhas com dados de apenas uma fonte.
-- Como a juncao afeta as quantidades e os valores ausentes?
-- TODO: consulta

-- 5. Compare as duas medidas de carga sem presumir equivalencia.
-- Registre unidade, grupos e periodo da comparacao.
-- TODO: consulta

-- 6. Consulte metadados da staging para demonstrar a origem das medidas.
-- TODO: consulta

-- 7. Reexecute a integracao e compare contagens e chaves.
-- Explique a politica de escrita que permite repetir o processo.
-- TODO: consultas antes/depois
