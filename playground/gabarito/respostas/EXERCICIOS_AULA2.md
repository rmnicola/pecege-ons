# Solucoes - Exercicios da Aula 2

Respostas observadas no pipeline real da copia de laboratorio.

1. Duplicatas por tipo: `duplicata_exata` 2; `conflito_chave` 2.

2. Categorias fora do padrão:

   | fonte | campo | valor_bruto | n | canônico |
   |---|---|---|---|---|
   | balanco | id_subsistema | ` s ` | 1 | S |
   | balanco | id_subsistema | `n` | 1 | N |
   | balanco | nom_subsistema | `SUDESTE/CENTRO-OESTE` | 169 | SUDESTE |
   | balanco | nom_subsistema | `nordeste` | 1 | NORDESTE |
   | curva | id_subsistema | ` s ` | 1 | S |
   | curva | nom_subsistema | `nordeste` | 1 | NORDESTE |

   (O 169 de SE é o nome real da fonte balanço, que difere da curva; é
   inconsistência entre fontes, não defeito injetado.)

3. Lacunas: N em `2025-01-03 05:00:00`, uma ocorrência por fonte.

4. Extremos: 4 no total. Dois vao para a quarentena DIDATICA (SE 2025-01-05
   18:00, valor 2176462.2, > 10x a mediana — criterio operacional didatico,
   nao prova de impossibilidade fisica) e dois do S em 2025-01-01 00:00/01:00
   (val_gertermica 333.262/303.397) apenas `extremo_revisar` — **mantidos**
   (presentes no snapshot original).

5. Quarentena: 13 registros — `conflito_chave` 4, `duplicata_exata` 2,
   `numero_invalido` 3, `celula_vazia` 2, `extremo_quarentena_didatica` 2.

6. Impacto (`SE`, `val_carga`): pico naive 2176462.2 -> tratado 51471.444;
   média naive 55213.6252 -> tratado 42550.5388.

7. Padronizações (limpo_balanco): `id_padronizado` = 2,
   `nome_padronizado` = 168, `numero_convertido` = 1.

Observação: como a chave SE 2025-01-04 12:00 foi para quarentena, ela vira
lacuna; por isso a cobertura tratada do SE cai de 168 para 166 no balanço.
