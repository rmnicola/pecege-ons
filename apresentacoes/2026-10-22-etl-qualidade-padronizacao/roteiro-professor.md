# ETL II — roteiro do professor

Primeira versão do deck novo (18/10/2026): 32 slides. O deck anterior, da proposta antiga, foi substituído; o material antigo da aula 2 no playground foi apagado (fica no histórico do git).

## Tempos

| Horário | Slides | Bloco |
|---|---|---|
| 09h00–09h05 | 1–4 | Capa, aviso, agenda; retomada: a transformação como peça (`Transformada`), com `ParquetS3` entrando no destino |
| 09h05–09h50 | 5–14 | O que se conserta: princípios; três jeitos de faltar; imputação (gráfico com três métodos); duplicata exata × conflito; texto que parece número; categorias e unidades; extremos (faixa mediana ± 5 MAD); junção com validação; caixa de ferramentas em pandas |
| 09h50–10h15 | 15–17 | O laboratório: o que mudou; `git pull` + `./preparar.sh`; começar |
| 10h15–10h30 | 18 | Intervalo |
| 10h30–11h35 | 19–21 | Desafio: parte 1 (dados limpos, até ~11h10) e parte 2 (Parquet no S3) |
| 11h35–11h55 | 22–26 | Warehouse, lake, lakehouse; o playground como lake em miniatura; Databricks; expectations |
| 11h55–12h00 | 31–32 | Encerramento e referências |

Os slides 27–30 (solução) são para consulta depois da aula, com a interrogação explicando cada trecho; não há demonstração.

## Playground

- Carga: `laboratorio.curva_horaria` (texto, defeitos C13–C22). Clima: `api-clima` (`servicos/api_clima.py`), defeitos fixos sobre respostas reais salvas. Armazenamento: RustFS 1.0.3 (a MinIO deixou de distribuir imagens públicas).
- Ponto de partida: `aluno/aula2/` (pipeline da aula 1 com `Transformada`, esqueletos com dicas). Solução: `gabarito/aula2/`; defeitos e regras: `gabarito/aula2/defeitos.md`.
- Resultado esperado: 672 linhas, 5 horas de carga e 6 de temperatura imputadas; Parquet em `s3://aula2/carga_clima/dados.parquet`. Conferido por `tests/test_aulas.py`.

## Cuidados

- Os exemplos dos slides 7–12 são sintéticos e não reproduzem os defeitos do desafio.
- Ao apresentar o Databricks, os nomes dos produtos foram conferidos em 18/10/2026 na documentação (Lakeflow Connect, Lakeflow Spark Declarative Pipelines, expectations, Lakeflow Jobs, Unity Catalog). O código do slide 26 é um esboço ilustrativo.
- Ao mencionar defeitos, deixar claro que não estão nas bases oficiais do ONS.
