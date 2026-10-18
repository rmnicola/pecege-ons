# Solucoes - Exercicios da Aula 1

Respostas observadas no pipeline real (recorte 2025-01-01..2025-01-08).

1. Linhas integradas em `aula1.integrado`:
   - total 840; subsistemas físicos 672; agregado SIN 168.

2. Unicidade da chave `(id_subsistema, din_instante)`:
   - a consulta com `HAVING count(*) > 1` retorna 0 linhas; há PK declarada.

3. Divergências entre as medidas de carga:
   - 0. No recorte (e em todo 2025) `val_carga = val_cargaenergiahomwmed`.
   - Explique: coincidência verificada, não equivalência assumida.

4. Picos por subsistema (valores reais do recorte, MWmed):

   | Subsistema | pico balanço `val_carga` | pico curva |
   |---|---|---|
   | N | 8326.01 | 8326.01 |
   | NE | 15825.672 | 15825.672 |
   | S | 17355.435 | 17355.435 |
   | SE | 51471.444 | 51471.444 |

5. Rastreabilidade: `_fonte_servico = fonte-balanco`,
   `_tabela_origem = balanco_horario`, `_sha256_recorte` =
   `cc625b2715d2bc4c4c266cb772f1815acf46c82a78b6d9c97dd768fe4ad4a849`.

6. Resíduo máximo `SIN - soma(subsistemas)`:
   - 0.005 MWmed (arredondamento de publicação). Não é erro; é diagnóstico.
