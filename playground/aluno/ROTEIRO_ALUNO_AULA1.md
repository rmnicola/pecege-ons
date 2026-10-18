# Aula 1 — roteiro do aluno

Preparação do ambiente: https://rmnicola.github.io/pecege-ons/aulas/2026-10-20-etl-i/preparacao/ (resumo: `./preparar.sh` dentro de `playground/`).

Todos os comandos abaixo rodam dentro de `playground/`.

## 1. Extrair a carga

```sh
docker compose run --rm etl python aluno/aula1/extrair_carga.py
```

Confira quantas linhas chegam por subsistema, que tipos chegam no instante e na carga e se o período cobre 01 a 07/01/2025.

## 2. Extrair o clima

```sh
docker compose run --rm etl python aluno/aula1/extrair_clima.py
```

Uma cidade por subsistema (Belém, Recife, São Paulo, Porto Alegre), uma simplificação: a temperatura de uma cidade não representa a região inteira. Confira quantas horas chegam por cidade, se batem com as horas de carga e onde vem a unidade.

## 3. Desafio: carga + temperatura

Complete `aluno/aula1/combinar.py` e gere `saida/dados.csv`, uma linha por subsistema e hora:

```
id_subsistema,instante,carga_mwmed,temperatura_c
```

```sh
docker compose run --rm etl python aluno/aula1/combinar.py
```

Use pandas. Fuso assumido: America/Sao_Paulo. Antes de gravar, confira quantas linhas o CSV deve ter, se a junção mudou o número de linhas e se sobrou alguma hora sem temperatura.

Sem internet? As respostas da Open-Meteo para o período estão salvas em `aluno/aula1/dados/` (veja o README da pasta).
