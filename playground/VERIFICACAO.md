# Verificacao - laboratorio ETL Pecege-ONS

Registro dos comandos realmente executados e dos resultados observados.
Nada aqui foi inferido: os numeros vem das execucoes reais dos containers.

> **Reexecutado pelo agente principal em 13/10/2026.** O pipeline dos dois
> cenários foi executado duas vezes em PostgreSQL real depois dos ajustes de
> terminologia, chave normalizada, parsing finito e transação do tratamento.
> Contagens idênticas: `840,838,670,838,13,4`; integração bruta da aula2
> rejeitada com código2; **20 testes passaram**(9 unitários +11 invariantes).
> Os slides e materiais do aluno não apresentam resultados ou gabaritos.

## Ambiente

```
Docker:   29.7.2 (client e server)
Compose:  v5.5.1
Imagens:  postgres:16-alpine, python:3.12-slim, pecege-ons-etl:local
Python (container): 3.12; psycopg 3.2.3; pytest 8.3.3
```

Permissoes: o servico `etl` roda como `user: ${ETL_UID:-1000}:${ETL_GID:-1000}`.
Conferido no host com `ls -ln` (execucao anterior): os arquivos em `resultados/`
ficaram com uid:gid `1000:1000`, **sem arquivos root-owned**.

## Snapshots e proveniencia (internet real)

`python3 scripts/tools/baixar_snapshot.py` (executado no host, com internet):

| Fonte | Linhas anuais | sha256 origem (CSV anual) | Linhas recorte | sha256 recorte |
|---|---|---|---|---|
| balanco | 43800 | `69c163bca9c02c3ad256dca4ca390fc17922040ce7bb1341f85f0d0e770d2eac` | 840 | `cc625b2715d2bc4c4c266cb772f1815acf46c82a78b6d9c97dd768fe4ad4a849` |
| curva | 35040 | `69a3d2560bf111e46d1fa356ee4be7c917ca89bf53ae16ab1af9f9e7477ff4c4` | 672 | `9a99e6557dbea2f0ec12943f04ae13fb4981351550572271a74297ea65616047` |

O hash de origem cobre o CSV anual inteiro (baixado em streaming e descartado);
o hash de recorte cobre somente o arquivo gravado. Verificado em
`data/oficial/PROVENIENCIA.json` e nos testes (`test_rastreabilidade...`).

Cobertura do recorte [2025-01-01 00:00, 2025-01-08 00:00): 168 horas, todos
os subsistemas (balanco: N, NE, S, SE, SIN; curva: N, NE, S, SE).

## Build e subida

```
docker compose config --quiet          -> OK
docker compose build etl               -> imagem pecege-ons-etl:local
docker compose up -d --wait ...        -> 3 bancos healthy
docker compose ps                      -> portas apenas internas (5432/tcp)
```

## Pipeline real (execucao 1 = execucao 2)

Comandos (todos `docker compose run --rm etl python <script>`):

```
00_carregar_fontes.py
01_extrair_balanco.py --cenario aula1 ; 02_extrair_curva.py --cenario aula1
03_integrar.py --cenario aula1
01_extrair_balanco.py --cenario aula2 ; 02_extrair_curva.py --cenario aula2
04_diagnosticar.py ; 05_tratar.py ; 06_avaliar.py
```

Contagens observadas nas duas execucoes (idempotencia):

```
aula1.integrado            = 840
aula2.limpo_balanco        = 838
aula2.limpo_curva          = 670
aula2.integrado_limpo      = 838
aula2.quarentena           = 13
aula2.diagnostico_extremos = 4
exec1 = exec2 = 840,838,670,838,13,4  -> igual = true
```

Detalhes da carga (00): balanco oficial 840 / laboratorio 841;
curva oficial 672 / laboratorio 673.

### Aula 1 - integracao

```
aula1.integrado: 840 linhas = 672 subsistemas + 168 agregado SIN
divergencias val_carga x val_cargaenergiahomwmed = 0
residuo max SIN vs soma dos subsistemas = 0.005 MWmed
```

Observacao verificada: em TODO o ano de 2025 as duas medidas de carga
coincidem exatamente (0 divergencias em 35.040 linhas). Isso e um resultado
da verificacao, nao uma equivalencia assumida.

### Aula 2 - diagnostico / tratamento / avaliacao

Defeitos (manifesto `gabarito/MANIFESTO_LABORATORIO.json`, 22 no total):

```
categoria_caixa_espaco 5 | numero_invalido 3 | celula_vazia 2
formato_decimal 2 | formato_data 2 | hora_faltante 2
duplicata_exata 2 | conflito_chave 2 | extremo_suspeito 2
```

Quarentena (13): conflito_chave 4, duplicata_exata 2, numero_invalido 3,
celula_vazia 2, extremo_quarentena_didatica 2.

Lacunas registradas (nao fabricadas): N 2025-01-03 05:00 nas duas fontes.

Extremos: 2 vao para a quarentena DIDATICA (SE 2025-01-05 18:00 = 2176462.2;
criterio de mediana/negativo, que NAO prova impossibilidade fisica) + 2 picos
termicos do S (333.262 / 303.397 MWmed) apenas `extremo_revisar`, pois estao
**presentes no snapshot original** e ficam mantidos para revisao.

Impacto (SE, val_carga):

| cenario | cobertura | media | pico |
|---|---|---|---|
| referencia | 168 | 42559.7869 | 51471.444 |
| naive | 169 | 55213.6252 | 2176462.2 |
| tratado | 166 | 42550.5388 | 51471.444 |

### Rejeicao da integracao ingenua (aula2)

```
docker compose run --rm etl python scripts/03_integrar.py --cenario aula2
exit code = 2
aula2.integracao_rejeitada = 4 (2 duplicata_exata + 2 conflito_chave)
```

### Exercicio de parametro e imputacao

- `mult_iqr = 3` -> 7 extremos suspeitos (default 8 -> 4); valores presentes
  no snapshot original entram so como "revisar", nada removido.
- `--imputar` -> limpo_balanco 840, limpo_curva 672, 4 imputacoes com metadado
  `mediana_hora_do_dia` e flag; lacunas passam a `imputado = true`. Preenche
  SOMENTE lacunas (nao altera celulas existentes); min/max e limite de VALOR,
  nao de tamanho de lacuna.

## Testes automatizados

```
docker compose run --rm etl python -m pytest tests -q
11 passed
```

Cobrem: integracao limpa (linhas/unicidade), medidas separadas, rejeicao da
integracao suja, lacunas sem zeros fabricados, padronizacao de categorias,
indicadores de impacto, decisoes de tratamento (gabarito), idempotencia,
rastreabilidade/origem nao alterada, servicos/bases separados, manifesto vs
dados.

## Bloqueios / limitacoes

- Sem `git` no diretorio, nao foi possivel gerar `git diff --stat`; o inventario
  de arquivos com linhas/bytes esta no relatorio final.
- `data/clean_ref/` e o proprio recorte oficial congelado; e um oracle de
  avaliacao, nao um gabarito de limpeza para producao.
