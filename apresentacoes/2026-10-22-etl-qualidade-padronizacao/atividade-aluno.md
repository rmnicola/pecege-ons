# Atividade — qualidade e transformação

## Objetivo

Avaliar dados de entrada cuja qualidade ainda não conhecemos, propor regras explícitas e verificar se a saída tratada pode ser usada no pipeline. Os problemas foram inseridos na cópia de exercício; os arquivos oficiais estão preservados.

## Materiais

- [`Roteiro operacional da aula2`](../../playground/aluno/ROTEIRO_ALUNO_AULA2.md).
- [`Consultas para preencher`](../../playground/aluno/exercicios_aula2.sql).
- [`Parâmetros do tratamento`](../../playground/aluno/parametros_aula2.json).
- [`Dicionários e proveniência`](../../playground/data/oficial/).

## Tarefas

1. Extraia as duas fontes com `--cenario aula2` (scripts 01 e 02). Inspecione o conteúdo recebido como texto antes de propor transformações.
2. Execute `03_integrar.py --cenario aula2`. A rejeição é esperada: investigue a causa e o contrato que impede a integração 1:1.
3. Execute `04_diagnosticar.py` e consulte `aula2.diagnostico_*` com as suas consultas SQL. Distinga célula nula, registro ausente, formato e valor suspeito; registre hipótese e evidência.
4. Para cada problema selecionado, defina regra e ação: converter, sinalizar, preservar, colocar em quarentena ou buscar informação adicional. Justifique com a evidência observada.
5. Execute `05_tratar.py`. Ele também integra a saída tratada depois de verificar a unicidade. Compare sua política com a implementação e mantenha o original rastreável.
6. Execute `06_avaliar.py`. Investigue efeitos sobre chaves, cobertura e indicadores, especificando grupo, medida, unidade e denominador.

### Experimento com parâmetros

Edite `aluno/parametros_aula2.json`, um parâmetro por vez, e reexecute 04, 05 e 06:

- `mult_iqr` e `fator_mediana`: mudam o que é sinalizado ou enviado à quarentena didática. Registre a hipótese: limiar estatístico indica suspeita, não prova impossibilidade física.
- `imputar`: extensão opcional. Preenche somente lacunas de registro pela mediana da mesma hora-do-dia, com flag; não altera células existentes. Registre hipótese, grupo e limite.

Restaure os parâmetros iniciais ao terminar e guarde o arquivo utilizado como evidência.

## Entrega

| Problema | Evidência | Regra e ação | Efeito observado | Limitação |
|---|---|---|---|---|
| Preencher com sua investigação | | | | |

Entregue também as consultas e os parâmetros utilizados. Explique quais dados podem ser publicados, exigem uso restrito ou devem ser rejeitados/investigados. Não há números de gabarito neste enunciado. A referência limpa é recurso didático para avaliar efeitos, não uma regra automática de produção. Imputação, se estudada, precisa de hipótese, grupo, limite e identificação dos valores inferidos.
