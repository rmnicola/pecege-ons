# Aula 1 — roteiro operacional do aluno

## Preparação antes da aula

Instale Docker Desktop (Windows/macOS) ou Docker Engine com Compose (Linux). Leia `../README.md`. A partir de `playground/`, com internet para preparar as imagens:

```sh
docker compose build etl
docker compose up -d --wait fonte-balanco fonte-curva destino
docker compose run --rm etl python scripts/00_carregar_fontes.py
```

O `00` carrega as fontes e reinicia resultados por padrão; execute apenas no setup/reset intencional. Os snapshots locais permitem trabalhar sem internet depois da preparação.

## 1. Identificar fontes e contratos

Localize no Compose `fonte-balanco`, `fonte-curva` e `destino`. Consulte os dicionários em `data/oficial/`. Registre tabelas, campos, tipos, identidade de uma linha, unidades e cobertura; verifique isso, não assuma equivalência pelo nome.

## 2. Extrair separadamente

```sh
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula1
docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula1
```

Antes de executar, identifique conexão, recorte e tabela escrita. Depois consulte `aula1.stg_balanco`, `aula1.stg_curva` e os registros em `resultados/`. Explique como demonstrar origem e repetir a extração.

## 3. Inspecionar e propor integração

```sh
docker compose exec destino psql -U ons_lab -d analytics
```

Escreva as consultas em `aluno/exercicios_aula1.sql` e execute-as no terminal SQL. Investigue unicidade, tipos, períodos e grupos. Justifique a chave e a política de junção, incluindo registros sem correspondência. Não substitua medidas ausentes por zero nem combine cargas sem verificar suas definições.

## 4. Integrar e carregar

```sh
docker compose run --rm etl python scripts/03_integrar.py --cenario aula1
```

Consulte `aula1.integrado`. Compare leitura e escrita, examine registros sem par e explique o efeito da junção. Reexecute e confira o efeito na saída.

## Entrega

Consultas e breve descrição de fontes, chave, granularidade, recorte, metadados, política de escrita e verificações. Os comandos estão prontos; a investigação e as justificativas são o trabalho da dupla. Não há respostas nem contagens de gabarito neste roteiro.
