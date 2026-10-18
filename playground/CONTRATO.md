# Contrato de integração — playground ETL Pecege–ONS

Este contrato coordena as duas apresentações e o laboratório. As fontes são cópias locais dos datasets oficiais do ONS; as instâncias PostgreSQL são uma arquitetura **didática**, não a arquitetura interna do ONS.

## Dados e proveniência

- Balanço: https://dados.ons.org.br/dataset/balanco-energia-subsistema
- Curva: https://dados.ons.org.br/dataset/curva-carga
- Recorte preferencial: 01/01/2025 00:00 (inclusive) a 08/01/2025 00:00 (exclusive), todos os subsistemas presentes. Confirmar a cobertura real ao baixar; não preencher horas silenciosamente.
- CSVs de origem: `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_2025.csv` e `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/curva-carga-ho/CURVA_CARGA_2025.csv`.
- Dicionários JSON oficiais nos mesmos diretórios: `DicionarioDados_Balanco_Energia_Subsistema.json` e `DicionarioDados_CurvaCarga.json`.
- Balanço: `id_subsistema`, `nom_subsistema`, `din_instante`, `val_gerhidraulica`, `val_gertermica`, `val_gereolica`, `val_gersolar`, `val_carga`, `val_intercambio`.
- Curva: `id_subsistema`, `nom_subsistema`, `din_instante`, `val_cargaenergiahomwmed`.
- Medidas dos dicionários em MWmed. Não presumir equivalência entre `val_carga` e `val_cargaenergiahomwmed`; mantê-las separadas e mostrar divergências como diagnóstico, não erro automático. Não impor geração = carga: existe intercâmbio e a interpretação depende da documentação.
- Preservar snapshots oficiais CSV/JSON em `playground/data/oficial/`, com metadados de URL, instante de extração e hash. Nenhum defeito artificial deve ser atribuído à base oficial.

## Serviços Docker Compose

Em `playground/compose.yaml`:

- `fonte-balanco`: PostgreSQL, banco `balanco`, tabela `oficial.balanco_horario`, cópia alterada `laboratorio.balanco_horario`.
- `fonte-curva`: PostgreSQL, banco `curva`, tabela `oficial.curva_horaria`, cópia alterada `laboratorio.curva_horaria`.
- `destino`: PostgreSQL, banco `analytics`, schemas separados `aula1` e `aula2` para staging, integrado e resultados.
- `etl`: ambiente Python containerizado com cliente PostgreSQL e bibliotecas necessárias; scripts e saídas montados. O usuário não precisa instalar Python nem cliente PostgreSQL no host.
- Bancos distintos em serviços distintos; scripts consultam seus hosts separadamente. Contas e senhas de laboratório configuradas no Compose e documentadas como credenciais locais de exercício. Evitar portas do host desnecessárias e conflitos com PostgreSQL já instalado.

## Comandos estáveis para as apresentações

Executar a partir de `playground/`:

```sh
docker compose up -d --wait fonte-balanco fonte-curva destino
docker compose run --rm etl python scripts/00_carregar_fontes.py

docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula1
docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula1
docker compose run --rm etl python scripts/03_integrar.py --cenario aula1

docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula2
docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula2
docker compose run --rm etl python scripts/04_diagnosticar.py
docker compose run --rm etl python scripts/05_tratar.py
docker compose run --rm etl python scripts/06_avaliar.py
```

Aula 1 extrai dos schemas `oficial`; aula 2 dos schemas `laboratorio`. A integração só acontece depois de verificar unicidade e cardinalidade. No cenário aula2, a integração ingênua deve ser diagnosticada/rejeitada; o tratamento deve documentar decisões antes de integrar.

## Requisitos pedagógicos

- Primeira metade das duas aulas: intuição e decisões de ETL, sustentadas por exemplos visuais curtos. Após intervalo de 10h15 a 10h30, prática com Docker/PostgreSQL.
- O professor é o fio condutor; telas com poucas palavras, diagramas, pequenos trechos de código e perguntas. Procedimentos completos, comandos e respostas em notas/roteiro/README, não projetados em parágrafos.
- Os slides podem mostrar o nome de um script e sua função, deixando o comando longo nas notas e no roteiro do aluno.
- Preparação antecipada: Docker Desktop ou Engine + Compose, download/build das imagens e teste do setup antes da aula. Na aula, confirmar setup e seguir para extração; reservar alternativa para acompanhar a demonstração se alguém não conseguir executar.
- Aula 2 contém casos reais da cópia didática: ausências, horas faltantes, duplicatas exatas e conflitos de chave, categorias/formatação, números inválidos e extremos suspeitos. Problemas precisam ser determinísticos, documentados em manifesto reservado ao professor e testados.
- Não ensinar remoção automática de picos, imputação global ou `drop_duplicates` indiscriminado. Preservar valor original, marcar alterações e quarentena. Comparar média, pico e cobertura com a referência limpa, sem fabricar conclusões nos slides.
- Entregar roteiro do aluno com tarefas; solução e gabarito do professor separados. Scripts de extração devem funcionar; exercícios podem pedir pequenas alterações em arquivos de aluno, não deixar toda a infraestrutura incompleta.

## Entregáveis

1. `apresentacoes/2026-10-20-etl-fontes-integracao/deck.html` e `dist/index.html`, notas, roteiro e QA.
2. `apresentacoes/2026-10-22-etl-qualidade-padronizacao/deck.html` e `dist/index.html`, notas, roteiro e QA.
3. `playground/`: Compose, scripts, snapshots/dicionários/metadados, atividades, soluções, testes de invariantes e instruções para máquinas Windows/macOS/Linux.

Se o laboratório precisar alterar esse contrato por um fato observado nos dados ou restrição técnica, comunique a mudança para integrar os dois decks; não modifique nomes de comandos silenciosamente.
