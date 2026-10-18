# Roteiro do professor - Laboratorio ETL Pecege-ONS

Material reservado. Nao distribua esta pasta nem o manifesto aos alunos.

## Antes da aula (com internet)

```sh
cd playground
docker compose config
docker compose build etl
docker compose up -d --wait fonte-balanco fonte-curva destino
docker compose run --rm etl python scripts/00_carregar_fontes.py
```

Se o snapshot `data/oficial/` estiver ausente ou voce quiser rebaixar:

```sh
docker compose run --rm etl python scripts/tools/baixar_snapshot.py
python3 scripts/tools/gerar_laboratorio.py     # regenera a copia suja deterministica
```

O snapshot oficial e o bundle local: os alunos **nao precisam de internet** na
aula, apenas das imagens ja construidas (postgres:16-alpine, python:3.12-slim,
pecege-ons-etl:local). Rode o pipeline uma vez antes para aquecer o cache.

## Sequencia e timing (aula de 165 min uteis)

| Bloco | Tempo | Conteudo |
|---|---|---|
| Abertura | 15 min | Contexto, datasets, arquitetura didatica (fonte x destino) |
| Teoria Aula 1 | 30 min | Extração, formatos, carga, rastreabilidade, integração 1:1 |
| Intervalo | 15 min | (10h15-10h30) |
| Pratica Aula 1 | 30 min | `00`, `01`, `02`, `03` (ver `aluno/ROTEIRO_ALUNO_AULA1.md`) |
| Teoria Aula 2 | 25 min | Ausências, duplicidade, extremos, padronização, impacto |
| Pratica Aula 2 | 45 min | `01/02 --cenario aula2`, `04`, `05`, `06`, extras |
| Fechamento | 5 min | Referências e leitura |

Cada script roda em menos de 1 segundo; o tempo e dedicado a discutir as
decisões. Abra o `psql` do destino para conferir resultados ao vivo.

## O que o laboratorio demonstra

- Duas fontes PostgreSQL **separadas** e um destino; conexões nomeadas por DNS
  do Compose (`fonte-balanco`, `fonte-curva`, `destino`); sem portas no host.
- Extração preserva o cru e registra origem/hash/timestamp.
- Integração só após verificar unicidade e cardinalidade; medidas de carga
  separadas; SIN como agregado.
- Cópia de laboratorio com **22 defeitos deterministicos** (ver manifesto).
- Diagnóstico sem limpar, tratamento com políticas explícitas, quarentena e
  flags, avaliação por impacto (média, pico, cobertura) contra a referência.

## Fato importante sobre o recorte 2025

Verificamos que `val_carga` (balanco) e `val_cargaenergiahomwmed` (curva)
**coincidem exatamente** em todas as 672 linhas do recorte e nas 35.040 linhas
de 2025 (0 divergências, diferença máxima 0). Ensine isso como **resultado da
verificação**, nunca como hipótese: o contrato pede mantê-las separadas e
mostrar divergências, e aqui não há divergência. Use como gancho para
"não confunda coincidência do recorte com equivalência conceitual".

## Armadilhas a reforçar

- **Não** remover picos automaticamente. O filtro IQR marca dois picos
  térmicos do S como "extremo_revisar" — eles ficam (presentes no snapshot
  original, mantidos para revisão).
- **Não** impor geração = carga; há intercâmbio (o diagnóstico mostra).
- **Não** usar `clean_ref` como gabarito automático de limpeza; ela é oracle
  de avaliação. As decisões de produção citam diagnóstico/evidência.
- Só imputar com hipótese, grupo e limite explícitos, com flag (default off).
- A cópia de laboratório é didática: nenhum defeito é da base oficial.

## Regenerar / resetar

```sh
docker compose run --rm etl python scripts/00_carregar_fontes.py   # reset deterministico
```

Para apagar tudo deste projeto (inclusive volumes):

```sh
docker compose down -v
```

## Falhas comuns

- `permission denied` ao gravar em `resultados/` no Linux: ajuste
  `ETL_UID`/`ETL_GID` em `.env` para o seu `id -u`/`id -g`.
- Porta 5432 ocupada: não é problema; **não publicamos portas**.
- Internet caiu na aula: não é necessária; o snapshot está versionado.
