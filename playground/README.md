# Laboratorio ETL Pecege-ONS

Ambiente didatico com **duas fontes PostgreSQL** (Balanco de Energia e Curva de
Carga Horaria, do Portal de Dados Abertos do ONS), um **destino** (analytics) e
um **container Python** de ETL. Roda o pipeline completo sem instalar Python
nem PostgreSQL no seu computador.

Leia tambem `CONTRATO.md` (contrato de integracao com as apresentacoes).

## Requisitos

- Docker Desktop (Windows/macOS) ou Docker Engine + Compose (Linux).
- Docker Compose v2 (`docker compose ...`).
- ~1 GB de espaco para as imagens. **Instale e baixe as imagens antes da
  aula.** Durante a aula nao e preciso internet: os dados ja estao em
  `data/oficial/`.

Verifique a instalacao:

```sh
docker --version
docker compose version
docker compose config --quiet && echo "compose OK"
```

Em Linux, se ao gravar em `resultados/` aparecer erro de permissao, copie
`.env.example` para `.env` e ajuste `ETL_UID`/`ETL_GID` para a saida de
`id -u` e `id -g`. Nos ultimos testes usamos Docker 29.7.2 e Compose 5.5.1.

## Preparar (uma vez, com internet)

```sh
docker compose build etl
docker compose up -d --wait fonte-balanco fonte-curva destino
```

Os tres bancos ficam `healthy`. Nenhuma porta e publicada no host, entao nao
ha conflito com um PostgreSQL que ja esteja rodando.

## Verificar o ambiente (aula ETL I)

```sh
docker compose run --rm etl python scripts/verificar_ambiente.py
```

Confere bibliotecas (psycopg, httpx, pandas), a fonte PostgreSQL via `PG_DSN`,
o acesso HTTPS a `archive-api.open-meteo.com` e a gravacao em `saida/`, pasta
onde a aula ETL I grava o CSV. Instrucoes para os alunos:
https://rmnicola.github.io/pecege-ons/aulas/2026-10-20-etl-i/preparacao/

## Pipeline

```sh
# 1) cria os schemas e carrega as fontes (idempotente; reseta destino)
#    ATENCAO: rodar de novo apaga os schemas aula1 e aula2 (resultados das
#    duas aulas). Rode UMA VEZ por sequencia; para so recarregar as fontes
#    sem perder os resultados, use --sem-reset.
docker compose run --rm etl python scripts/00_carregar_fontes.py

# 2) Aula 1 - fontes e integracao (schemas oficial)
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula1
docker compose run --rm etl python scripts/02_extrair_curva.py   --cenario aula1
docker compose run --rm etl python scripts/03_integrar.py        --cenario aula1

# 3) Aula 2 - qualidade e padronizacao (copia de laboratorio)
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula2
docker compose run --rm etl python scripts/02_extrair_curva.py   --cenario aula2
# checkpoint: a integracao INGENUA de aula2 deve ser REJEITADA (exit 2),
# ANTES de tratar. E o que mostra por que 03 exige unicidade/cardinalidade:
docker compose run --rm etl python scripts/03_integrar.py --cenario aula2   # exit 2 esperado
docker compose run --rm etl python scripts/04_diagnosticar.py
docker compose run --rm etl python scripts/05_tratar.py
docker compose run --rm etl python scripts/06_avaliar.py
```

Observacao sobre `--imputar` (em `05_tratar.py`): preenche **somente as
lacunas** (horas ausentes), pela mediana da mesma hora-do-dia do subsistema,
com flag. Ele **nao altera celulas existentes** (vazias/invalidas continuam
NULL + quarentena). O limite min/max registrado e o intervalo dos **valores**
observados do grupo, nao um limite de tamanho da lacuna: nao existe parametro
de tamanho maximo de lacuna.

Cada script imprime um resumo e grava um JSON em `resultados/`. O pipeline e
idempotente: rodar de novo nao duplica dados.

## Exercicios (aluno)

Preencha primeiro as consultas dos arquivos do aluno. Em Linux/macOS, os
comandos abaixo passam o arquivo preenchido pelo stdin ao PostgreSQL. No
PowerShell, use o terminal SQL interativo mostrado abaixo e execute as consultas.

```sh
# rodar as consultas da Aula 1 (no destino)
docker compose exec -T destino psql -U ons_lab -d analytics < aluno/exercicios_aula1.sql

# rodar as consultas da Aula 2
docker compose exec -T destino psql -U ons_lab -d analytics < aluno/exercicios_aula2.sql

# exercicio de parametro: edite aluno/parametros_aula2.json e reprocesse
# registre a hipotese e compare os efeitos, sem presumir melhora automatica
docker compose run --rm etl python scripts/04_diagnosticar.py
docker compose run --rm etl python scripts/05_tratar.py
docker compose run --rm etl python scripts/06_avaliar.py
```

Para inspecionar os resultados:

```sh
docker compose exec destino psql -U ons_lab -d analytics
# dentro do psql: \dt aula1.*   \dt aula2.*
```

Credenciais locais de exercicio (nao use em producao): usuario `ons_lab`,
senha `ons_lab`, bancos `balanco`, `curva` e `analytics`.

## Testes

```sh
bash tests/run_tests.sh
# unidade puros, sem Docker (nao precisam de psycopg):
python3 tests/test_unit_sem_docker.py
```

`run_tests.sh` roda o pipeline duas vezes (checando idempotencia), confirma a
rejeicao da integracao ingenua do cenario sujo e executa os invariantes com
`pytest`; `test_unit_sem_docker.py` testa parsing finito e classificacao de
duplicatas por chave normalizada.

## Estrutura

```
compose.yaml            Servicos fonte-balanco, fonte-curva, destino, etl
docker/etl/             Dockerfile (Python 3.12 + psycopg3) e dependencias
scripts/                Pipeline 00..06 e utilitarios em scripts/tools/
data/oficial/           Snapshot (+ PROVENIENCIA.json com URL/hash)
data/laboratorio/       Copia didatica com defeitos deterministicos
data/clean_ref/         Referencia limpa (oracle de avaliacao)
aluno/                  Roteiros e exercicios (SQL e parametros)
gabarito/              Roteiro, manifesto e gabaritos
tests/                  Invariantes e runner do pipeline
resultados/             Saidas geradas pelos scripts
```

## Encerrar

```sh
docker compose stop                 # para os containers, preserva volumes/saidas
docker compose down                 # remove containers e rede, preserva volumes
docker compose down -v              # remove tambem os volumes (reset total)
```

## Solucao de problemas

- **Internet caiu**: o snapshot local e suficiente; nao rode
  `scripts/tools/baixar_snapshot.py`.
- **Container `etl` nao conecta**: rode `docker compose up -d --wait` primeiro;
  o `connect` tem retry.
- **Imagens ausentes**: `docker compose pull` (bancos) e `docker compose build`.
- **Windows**: use PowerShell; os mesmos comandos `docker compose ...` valem.
