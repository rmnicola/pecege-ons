# Aula 2 — defeitos das fontes e regras da solução

Os defeitos são deliberados e fixos. Não são falhas das bases oficiais: a carga vem de `laboratorio.curva_horaria`, cópia didática da Curva de Carga do ONS (manifesto completo em `gabarito/MANIFESTO_LABORATORIO.json`, itens C13–C22); o clima vem da API local `servicos/api_clima.py`, que aplica os defeitos sobre respostas reais da Open-Meteo salvas em `aluno/aula1/dados/`.

## Carga (PostgreSQL, todas as colunas em texto)

| Item | Onde | Defeito | Regra da solução |
|---|---|---|---|
| C13, C14 | S 02/01 03h, NE 02/01 04h | Código com espaço ou caixa diferente | `strip().upper()` |
| C15 | SE 03/01 06h | Texto não numérico no valor | vira ausente e é imputado |
| C16 | SE 03/01 07h | Célula vazia | vira ausente e é imputado |
| C17 | N 04/01 08h | Vírgula decimal | troca por ponto antes de converter |
| C18 | N 03/01 05h | Hora inteira ausente | criada na grade horária e imputada |
| C19 | NE 02/01 10h | Duplicata exata | fica uma linha |
| C20 | SE 04/01 12h | Conflito de chave (43.125 × 48.125) | as duas saem; a hora é imputada |
| C21 | SE 05/01 18h | Extremo (2.176.462, ~50× a mediana) | desvio > 10 MAD do subsistema: ausente e imputado |
| C22 | SE 06/01 07h | Data com `T` | `pd.to_datetime(format="ISO8601")` |

## Clima (API local)

| Cidade | Defeito | Regra da solução |
|---|---|---|
| Belém (N) | `null` em 03/01 13h, 14h e 15h | imputado |
| Recife (NE) | `-999` em 04/01 02h e 05/01 22h | sentinela vira ausente e é imputado |
| São Paulo (SE) | série inteira em °F (`hourly_units`) | conversão para °C pela coluna `unidade` |
| Porto Alegre (S) | 02/01 10h repetida | fica a primeira |
| Porto Alegre (S) | 61,3 °C em 06/01 15h | fora de −10 a 50 °C: ausente e imputado |

## Resultado esperado

672 linhas (4 subsistemas × 168 horas). Imputação por interpolação linear dentro de cada subsistema, marcada em `carga_mwmed_imputado` (5 horas) e `temperatura_c_imputado` (6 horas). Conferido em 18/10/2026: `executar.py` grava o CSV e, com `--s3`, o Parquet em `s3://aula2/carga_clima/dados.parquet`.

Outras regras são defensáveis (descartar em vez de imputar, outro limite para extremos, manter o primeiro valor de um conflito). O que se avalia é a regra ser explícita, justificada e marcada no resultado.
