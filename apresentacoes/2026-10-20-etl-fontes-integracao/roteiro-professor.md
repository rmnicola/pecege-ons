# ETL I — roteiro em construção

A versão atual tem 16 slides. Os antigos slides 4 e 5 foram unidos no novo slide 4: notebook com leitura, amostra e resumo, seguido das revelações do CSV e de sua origem desconhecida. A legenda “Notebook inicial…” foi removida.

A agenda do cenário está no slide 15. A abertura solicitada como slide 17 passou a ser o slide 16 após a união: primeiro as duas fontes permanecem visíveis, PostgreSQL com carga elétrica e Open-Meteo com temperatura; um avanço revela setas convergentes e um único CSV com as duas informações.

A API escolhida para o cenário é Open-Meteo Historical Weather. Antes de extrair e integrar, discutir localidade/coordenadas, subsistema, período e convenção temporal. Temperatura de um ponto não representa automaticamente todo um subsistema. O histórico meteorológico é baseado em reanálise; não apresentá-lo como uma estação medida. Nenhuma relação estatística foi calculada nesta versão.

O restante da segunda parte continua em construção incremental: discutir uma parte, fechar a ideia e só então montar o próximo bloco. Cada futuro desafio será seguido de sua solução. O playground existente não foi alterado.

## Ajustes de 18/10/2026 (slides 1–16)

Decisão: o laboratório usará PostgreSQL (Curva de Carga) + Open-Meteo e gravará o CSV numa pasta local. MinIO (substituído por RustFS em 18/10/2026: a MinIO deixou de distribuir imagens públicas) fica para ETL II. O notebook do slide 4 já lê o contrato do `dados.csv` final (`id_subsistema`, `carga_mwmed`, `temperatura_c`). Os slides 11–12 usam o endpoint Historical Weather (`/v1/archive`), com `start_date`/`end_date` inclusivos, diferente do fim exclusivo da consulta PostgreSQL. As notas dos slides 13–14 antecipam o MinIO (API S3) da aula ETL II. Slide 8 sem sobreposição; legenda dos slides 9/11/13 à esquerda. Próxima parte: slides 17 em diante e implementação no playground.

## Plano revisado (18/10/2026)

ETL I: extração e transformação de um fluxo de extração em código componível (padrão Strategy com dependências injetadas). Prática: setup do ambiente → extrair carga (PostgreSQL) → extrair clima (Open-Meteo) → desafio de combinar e salvar `dados.csv` numa pasta → desafio de tornar o código componível. Sem MinIO.

ETL II: correções típicas de dados extraídos e carga no MinIO. Playground equivalente ao da ETL I, agora com defeitos deliberados nos dados; refazer o fluxo corrigindo e adequando ao padrão definido.

## Bloco do laboratório até o intervalo (18/10/2026)

Slides 15–18: ambiente (`./preparar.sh`), extração da carga e do clima com os arquivos de `playground/aluno/aula1/` (mesmo código dos slides 10 e 12) e agenda do intervalo. O formato do `dados.csv` (colunas `id_subsistema`, `instante`, `carga_mwmed`, `temperatura_c`; período 01–07/01/2025; fuso America/Sao_Paulo assumido; uma cidade por subsistema: Belém, Recife, São Paulo, Porto Alegre) entra no enunciado do Desafio 1. Com `evento` de 01/01 a 08/01, a carga traz 168 horas por subsistema e a Open-Meteo 192 por cidade, porque `end_date` é inclusivo: a pergunta "batem com as horas de carga? Por quê?" leva a turma a descobrir isso antes do Desafio 1.

## Revisão minimalista (18/10/2026)

Retirados: síntese "Foco desta aula" do CRISP-DM; "Nesta aula: extrair e carregar", destaque de E/L e miniícones do ETL; legenda, "Depois: carga na staging" e rodapé dos diagramas de fonte; coluna lateral e passos dos slides de código (a ajuda `?` percorre o código, com o restante do slide desfocado); slide do contrato; coluna "Pronto quando" do ambiente. Os links de documentação (Psycopg 3, Open-Meteo Historical Weather, HTTPX) vão para o slide final de referências.

## Depois do intervalo: desafio e solução (18/10/2026)

10h30–11h30 · Desafio (slide 20): completar `playground/aluno/aula1/combinar.py` (esqueleto com cinco passos e dicas, sem a resposta) e gerar `saida/dados.csv`. Armadilhas a descobrir: 168 × 192 horas (`end_date` inclusivo), `Decimal` e `datetime` × texto, tipo de junção.

11h30–11h55 · Solução, o professor programando com a turma: solução em dois slides (22–23), depois as peças que se encaixam (24, com dois avanços: ClimaArquivo e MinIO), o pipeline que só conhece contratos (25) e a troca de fonte sem mexer no pipeline (26). Os slides de código têm a interrogação explicando cada trecho, para consulta depois. Código final em `playground/gabarito/aula1/` (`combinar.py` e `componivel/`); `executar.py --offline` usa `ClimaArquivo` com as respostas salvas em `aluno/aula1/dados/`. As três versões geram o mesmo CSV (672 linhas), conferido em 18/10/2026.

11h55–12h00 · Encerramento e referências.
