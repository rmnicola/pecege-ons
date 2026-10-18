# ETL II — roteiro do professor

**Problema:** a extração chegou, mas a adequação dos dados ao uso ainda é desconhecida. A exposição reconstrói a decisão de aceitação em etapas — fronteira, contrato, diagnóstico, transformação, política e publicação — e a segunda parte aplica a mesma sequência no laboratório. Os slides da prática apresentam tarefas, nunca resultados.

## Preparação

Referências: Kimball/Caserta (*The Data Warehouse ETL Toolkit*, 2004) para limpeza, conformação e tratamento de exceções; [Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework) para adequação ao uso, dimensões e ciclo de vida; McKinney capítulos 7 e 8 para preparação e integração. Os scripts do playground usam psycopg e biblioteca padrão; os trechos de pandas são leitura complementar, não código anunciado como parte do laboratório.

Ambiente preparado antes do encontro. Reutilizar os bancos e snapshots da aula1; não executar `00` por rotina, pois ele reinicia resultados por padrão. A cópia `laboratorio` é deliberadamente alterada; não atribuir seus defeitos às bases oficiais. Não distribuir o manifesto/gabarito `playground/gabarito/` junto ao enunciado.

## Primeira parte — condução (09h00–10h15)

| Horário | Slides | Uso na explicação |
|---|---|---|
| 09h00–09h03 | 1–2 · Capa e aviso | Situar o escopo e o problema do dia |
| 09h03–09h09 | 3 · Da recepção ao uso | Marcar a fronteira: aceitar é decisão, não efeito da carga |
| 09h09–09h13 | 4 · Qualidade é adequação ao uso | Deslocar de “o dado é bom?” para “serve a este uso?” |
| 09h13–09h19 | 5 · Contrato de entrada | Esquema, identidade, cobertura e uso; tolerâncias vindas do uso |
| 09h19–09h24 | 6 · Esquema e identidade | Granularidade subsistema+instante; as duas medidas de carga separadas |
| 09h24–09h29 | 7 · Cobertura e grade esperada | Diferenciar hora ausente de célula vazia; não extrapolar a grade |
| 09h29–09h33 | 8 · Requisitos de uso | O que é indispensável e o que admite uso com restrição |
| 09h33–09h39 | 9 · Diagnóstico de qualidade | As dimensões como lentes para montar um perfil |
| 09h39–09h43 | 10 · Célula nula × registro ausente | Dois problemas distintos, dois tratamentos |
| 09h43–09h47 | 11 · Duplicata exata × conflito de chave | Classificar antes de agir; não escolher valor arbitrariamente |
| 09h47–09h51 | 12 · Formato × significado | Conversão não garante o mesmo significado |
| 09h51–09h55 | 13 · Consistência: geração × carga | Não impor geração=carga; há intercâmbio |
| 09h55–09h58 | 14 · Acurácia por evidência | Testes internos não provam acurácia; dois sistemas repetem erro |
| 09h58–10h02 | 15 · Duas classes de transformação | Padronização (representação) × conformação (significado) |
| 10h02–10h05 | 16 · Padronização | Regra explícita, flag e valor original preservado |
| 10h05–10h08 | 17 · Conformação | Códigos, unidades e definições; conformar antes de juntar |
| 10h08–10h11 | 18 · Política por problema | Tabela-mãe das quatro classes de problema |
| 10h11–10h13 | 19 · Representação e duplicidade | Conversão com flag; duplicata exata × conflito |
| 10h13–10h14 | 20 · Ausência | Ausência não é zero; imputação só com hipótese |
| 10h14–10h15 | 21 · Valor suspeito | Limiar estatístico não é impossibilidade física |
| — | 22 · Aceitação e publicação | Aceitar, restringir ou rejeitar, deixando rastro |
| — | 23 · Diagnóstico → política → publicação | Recapitular a sequência e fazer a ponte para a prática |
| 10h15–10h30 | 24 · Intervalo | 15 minutos |

> O bloco é denso por decisão do professor: os slides 16–23 podem ser acelerados ou usados como consulta, conforme o ritmo da turma. As referências de apoio ficam no slide final.

### Precisão durante a fala

- Qualidade é adequação a um propósito, não uma garantia universal de que o dado é verdadeiro.
- Testes internos de formato/consistência não comprovam acurácia; comparação requer referência apropriada e evidência confiável.
- A grade esperada permite identificar um registro horário ausente; uma célula vazia é outro problema.
- Classificar duplicatas antes da ação. Normalizar códigos/datas também pode revelar conflito de chave.
- Não substituir ausências por zero, escolher arbitrariamente uma versão de um conflito ou tratar todo pico como erro.
- Threshold de IQR/mediana identifica suspeita; não demonstra impossibilidade física. A quarentena automatizada do exercício é política didática, com critério e original registrados.
- Não impor geração igual a carga: existe intercâmbio e a interpretação depende da documentação.
- `val_carga` e `val_cargaenergiahomwmed` são medidas distintas e permanecem separadas.
- Imputação é inferência com hipótese e flag. Completude aparente não significa melhoria automática de qualidade.

## Segunda parte — atividade (10h30–12h00)

| Horário | Slides | Orientação |
|---|---|---|
| 10h30–10h38 | 25 · Ambiente | Explicar a cópia de exercício e a separação dos schemas |
| 10h38–11h00 | 26 · Extrair e testar | Extrair com `--cenario aula2`; observar a rejeição bruta esperada |
| 11h00–11h20 | 27 · Diagnosticar | Perfilar as staging; separar célula, registro, formato e suspeito |
| 11h20–11h38 | 28 · Tratar e integrar | Formular políticas; executar 05, que também integra |
| 11h38–11h50 | 29 · Avaliar e entregar | Rodar 06; comparar cenários; ajustar parâmetros e fechar a entrega |
| 11h50–12h00 | 29 e 30 | Duplas apresentam decisões; referências disponíveis |

Comandos, a partir de `playground/`:

```sh
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula2
docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula2
docker compose run --rm etl python scripts/03_integrar.py --cenario aula2
```

A última chamada deve rejeitar a integração bruta (código 2). Esse é um checkpoint de validação, não problema de setup. Pedir que a dupla investigue a causa; não revelar a lista de defeitos.

```sh
docker compose run --rm etl python scripts/04_diagnosticar.py
docker compose run --rm etl python scripts/05_tratar.py
docker compose run --rm etl python scripts/06_avaliar.py
```

`05` integra os dados tratados depois de verificar unicidade; não executar `03` sem cenário sobre a saída limpa. Ajustar um parâmetro por vez em `aluno/parametros_aula2.json`: `mult_iqr` e `fator_mediana` mudam a marcação de suspeitos; `imputar` é extensão opcional que preenche somente lacunas de registro pela mediana da mesma hora-do-dia, com flag — não altera células existentes, e min/max é limite de valor, não de comprimento da lacuna. Restaurar os valores iniciais ao final.

Material operacional: [`atividade-aluno.md`](atividade-aluno.md), [`ROTEIRO_ALUNO_AULA2.md`](../../playground/aluno/ROTEIRO_ALUNO_AULA2.md), exercícios SQL e parâmetros. Entrega: tabela de regras com evidência, registro das alterações/exceções e justificativa de aceitação da saída. Os números calculados e soluções ficam no gabarito reservado; não são conteúdo dos slides.
