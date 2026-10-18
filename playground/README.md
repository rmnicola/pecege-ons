# Laboratorio ETL Pecege-ONS

Ambiente didatico das aulas de ETL, todo em containers Docker: nao e preciso
instalar Python nem PostgreSQL no computador.

| Servico | Papel |
|---|---|
| `fonte-curva` | PostgreSQL com a Curva de Carga do ONS (`oficial.curva_horaria`) e uma copia com defeitos (`laboratorio.curva_horaria`) |
| `fonte-balanco` | PostgreSQL com o Balanco de Energia do ONS |
| `destino` | PostgreSQL de destino do pipeline de integracao |
| `api-clima` | API local no formato da Open-Meteo, com defeitos de proposito (aula 2) |
| `rustfs` | Armazenamento de objetos compativel com S3 (aula 2) |
| `etl` | Python 3.12 com psycopg, httpx, pandas, pyarrow e boto3 |

Passo a passo para os alunos:
https://rmnicola.github.io/pecege-ons/aulas/2026-10-20-etl-i/preparacao/

## Preparar

```sh
./preparar.sh
```

Registra seu usuario em `.env`, constroi a imagem, sobe os servicos, carrega os
dados se ainda nao estiverem carregados (sem apagar resultados), cria o bucket
`aula2` e roda a verificacao. Pode ser executado de novo a qualquer momento;
depois de um `git pull`, rode de novo para atualizar a imagem e os servicos.

A verificacao sozinha:

```sh
docker compose run --rm etl python scripts/verificar_ambiente.py
```

Requisitos: Docker Engine com Compose v2 (`docker compose`) e cerca de 1,5 GB
para as imagens. Testado com Docker 29.7.2 e Compose 5.5.1.

## Aula 1 — extracao e codigo componivel

```sh
docker compose run --rm etl python aluno/aula1/extrair_carga.py
docker compose run --rm etl python aluno/aula1/extrair_clima.py
docker compose run --rm etl python aluno/aula1/combinar.py      # desafio
```

Roteiro: `aluno/ROTEIRO_ALUNO_AULA1.md`. Respostas salvas da Open-Meteo para
trabalhar sem internet: `aluno/aula1/dados/`. Solucao: `gabarito/aula1/`
(`combinar.py` e o pipeline em pecas em `componivel/`).

## Aula 2 — transformacao e armazenamento S3

```sh
docker compose run --rm etl python aluno/aula2/executar.py
```

Parte 1: completar `aluno/aula2/transformacoes.py` ate gerar
`saida/dados_limpos.csv`. Parte 2: completar `ParquetS3` em
`aluno/aula2/destinos.py` e gravar em `s3://aula2/carga_clima/dados.parquet`.
Roteiro: `aluno/ROTEIRO_ALUNO_AULA2.md`.

API de clima local: `http://api-clima:8080/v1/archive` (dentro do compose).
Console do RustFS: http://localhost:9001/rustfs/console/ (usuario `ons_lab`,
senha `ons_lab_s3`); para outra porta, defina `RUSTFS_CONSOLE_PORT` no `.env`.

Solucao e defeitos documentados: `gabarito/aula2/`.

## Pipeline de integracao Balanco + Curva

Pipeline de referencia que integra as duas bases do ONS no PostgreSQL de destino:

```sh
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula1
docker compose run --rm etl python scripts/02_extrair_curva.py   --cenario aula1
docker compose run --rm etl python scripts/03_integrar.py        --cenario aula1
```

`scripts/00_carregar_fontes.py` recria as fontes e, por padrao, **apaga os
schemas de resultado do destino**; use `--sem-reset` para preservar.

## Testes

```sh
bash tests/run_tests.sh
python3 tests/test_unit_sem_docker.py   # unidade, sem Docker
```

`run_tests.sh` sobe os servicos, roda o pipeline de integracao duas vezes
(checando idempotencia) e executa com `pytest` os invariantes das fontes e os
testes das aulas: defeitos da API local, pipeline componivel da aula 1 sem
internet, solucao da aula 2 em CSV e em Parquet no S3.

## Estrutura

```
compose.yaml            Servicos (fontes, destino, api-clima, rustfs, etl)
preparar.sh             Setup completo e idempotente
docker/etl/             Dockerfile e dependencias Python
servicos/api_clima.py   API local de clima com defeitos (aula 2)
scripts/                Carga das fontes, pipeline de integracao, verificacao
data/oficial/           Recorte oficial do ONS (+ PROVENIENCIA.json)
data/laboratorio/       Copia didatica com defeitos deterministicos
aluno/                  Codigo inicial e roteiros das aulas
gabarito/               Solucoes, manifesto de defeitos e roteiros do professor
tests/                  Testes e runner
saida/, resultados/     Saidas geradas
```

## Encerrar

```sh
docker compose stop        # para os containers, preserva dados
docker compose down        # remove containers e rede, preserva volumes
docker compose down -v     # remove tambem os volumes (reset total)
```
