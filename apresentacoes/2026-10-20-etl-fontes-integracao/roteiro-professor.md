# ETL I — roteiro em construção

A versão atual tem 16 slides. Os antigos slides 4 e 5 foram unidos no novo slide 4: notebook com leitura, amostra e resumo, seguido das revelações do CSV e de sua origem desconhecida. A legenda “Notebook inicial…” foi removida.

A agenda do cenário está no slide 15. A abertura solicitada como slide 17 passou a ser o slide 16 após a união: primeiro as duas fontes permanecem visíveis, PostgreSQL com carga elétrica e Open-Meteo com temperatura; um avanço revela setas convergentes e um único CSV com as duas informações.

A API escolhida para o cenário é Open-Meteo Historical Weather. Antes de extrair e integrar, discutir localidade/coordenadas, subsistema, período e convenção temporal. Temperatura de um ponto não representa automaticamente todo um subsistema. O histórico meteorológico é baseado em reanálise; não apresentá-lo como uma estação medida. Nenhuma relação estatística foi calculada nesta versão.

O restante da segunda parte continua em construção incremental: discutir uma parte, fechar a ideia e só então montar o próximo bloco. Cada futuro desafio será seguido de sua solução. O playground existente não foi alterado.

## Ajustes de 18/10/2026 (slides 1–16)

Decisão: o laboratório usará PostgreSQL (Curva de Carga) + Open-Meteo e gravará o CSV numa pasta local. MinIO fica para ETL II. O notebook do slide 4 já lê o contrato do `dados.csv` final (`id_subsistema`, `carga_mwmed`, `temperatura_c`). Os slides 11–12 usam o endpoint Historical Weather (`/v1/archive`), com `start_date`/`end_date` inclusivos, diferente do fim exclusivo da consulta PostgreSQL. As notas dos slides 13–14 antecipam o MinIO (API S3) da aula ETL II. Slide 8 sem sobreposição; legenda dos slides 9/11/13 à esquerda. Próxima parte: slides 17 em diante e implementação no playground.

## Plano revisado (18/10/2026)

ETL I: extração e transformação de um fluxo de extração em código componível (padrão Strategy com dependências injetadas). Prática: setup do ambiente → extrair carga (PostgreSQL) → extrair clima (Open-Meteo) → desafio de combinar e salvar `dados.csv` numa pasta → desafio de tornar o código componível. Sem MinIO.

ETL II: correções típicas de dados extraídos e carga no MinIO. Playground equivalente ao da ETL I, agora com defeitos deliberados nos dados; refazer o fluxo corrigindo e adequando ao padrão definido.
