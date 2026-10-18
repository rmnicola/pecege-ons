# Aula 2 — roteiro do aluno

Todos os comandos rodam dentro de `playground/`.

## 0. Atualizar o ambiente

```sh
git pull
./preparar.sh
```

O script atualiza a imagem e sobe dois serviços novos: a API de clima local e o RustFS, um armazenamento de objetos compatível com S3. A verificação final mostra seis linhas `[OK]`.

## 1. Conhecer as fontes da aula 2

O código de `aluno/aula2/` é o pipeline em peças da aula 1, com duas fontes trocadas:

- `CargaPostgres` lê `laboratorio.curva_horaria`, uma cópia didática da Curva de Carga em que **todas as colunas chegam como texto**.
- `ClimaApi` consulta a API local (`CLIMA_URL`), no mesmo formato da Open-Meteo, e devolve também a coluna `unidade`.

As duas fontes trazem problemas de propósito. Eles não estão listados: investigue.

## 2. Desafio, parte 1: dados limpos

Complete `limpar_carga` e `limpar_clima` em `aluno/aula2/transformacoes.py` e rode:

```sh
docker compose run --rm etl python aluno/aula2/executar.py
```

O resultado é `saida/dados_limpos.csv`, uma linha por subsistema e hora (01 a 07/01/2025), com as colunas da aula 1 e duas marcas novas, `carga_mwmed_imputado` e `temperatura_c_imputado`, que dizem quais valores você preencheu ou substituiu.

Para cada correção, escreva a regra e o motivo num comentário. Não existe uma única resposta certa; existe regra explícita e justificada.

## 3. Desafio, parte 2: Parquet no S3

Complete `ParquetS3` em `aluno/aula2/destinos.py`, troque o destino em `executar.py` e rode de novo. O arquivo deve aparecer em `s3://aula2/carga_clima/dados.parquet`.

Para conferir no navegador: http://localhost:9001/rustfs/console/ (usuário `ons_lab`, senha `ons_lab_s3`).
