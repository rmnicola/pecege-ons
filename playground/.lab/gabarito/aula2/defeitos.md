# Aula 2 — falhas da carga e regras da solução

As falhas são deliberadas e fixas, inseridas em `laboratorio.curva_horaria` (`.lab/banco/curva_laboratorio.csv`), cópia didática do recorte de 01 a 07/01/2025 da Curva de Carga do ONS. Não são falhas da base oficial. A cópia está ordenada por subsistema e hora, como a interpolação do passo 5 precisa.

Cinco tipos de falha, cada um com um único tipo de defeito, repetido em algumas linhas:

| Passo | Tipo de falha | Onde | Regra da solução |
|---|---|---|---|
| 1 | Texto despadronizado | código `" s "` (S 02/01 3h), `"se"` (SE 03/01 14h), `"Ne "` (NE 05/01 9h), `" N"` (N 06/01 20h) | `str.strip().str.upper()` |
| 2 | Formato errado | vírgula decimal em N 04/01 8h, S 02/01 16h, SE 06/01 11h, NE 03/01 18h | troca por ponto e `pd.to_numeric(errors="coerce")` |
| 3 | Duplicidade | linha repetida, idêntica: NE 02/01 10h, SE 04/01 12h, N 05/01 15h | `drop_duplicates()` |
| 4 | Outlier | SE 05/01 18h (187.432,6), S 07/01 10h (121.905,3), N 02/01 12h (98.766,2); z entre 4,9 e 10,4, e o maior valor normal tem z = 1,96 | z-score de toda a carga; com \|z\| > 3, fica vazio |
| 5 | Dados faltantes | células vazias: SE 03/01 7h, NE 04/01 13h, S 05/01 22h | marca `carga_imputada` e interpola |

## Resultado esperado

672 linhas (4 subsistemas × 168 horas), sem vazios; 6 horas em `carga_imputada` (3 células vazias e 3 outliers), todas a menos de 2% do valor oficial. Nas outras 666 horas, a carga é igual à da base oficial. Conferido em 20/10/2026 com `python .lab/gabarito/aula2/limpar.py`, que grava `saida/carga_limpa.parquet` e o envia para `s3://aula2/carga/carga_limpa.parquet`.
