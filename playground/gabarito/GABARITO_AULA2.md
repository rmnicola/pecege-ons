# Gabarito da Aula 2 - defeitos, politicas e impacto

Fonte do manifesto: `gabarito/MANIFESTO_LABORATORIO.json` (gerado por
`scripts/tools/gerar_laboratorio.py`). Total: **22 defeitos**.

## Defeitos deterministicos

| ID | Arquivo | Tipo | Alvo (id, instante) | Campo | Valor no laboratorio | Tratamento |
|---|---|---|---|---|---|---|
| B01 | balanco | categoria caixa/espaco | S, 2025-01-02 03:00 | id_subsistema | ` s ` | trim+upper -> S; flag |
| B02 | balanco | categoria caixa/espaco | NE, 2025-01-02 04:00 | nom_subsistema | `nordeste` | upper+canonico -> NORDESTE |
| B03 | balanco | numero invalido | SE, 2025-01-03 06:00 | val_gertermica | `N/A` | NULL + quarentena |
| B04 | balanco | celula vazia | SE, 2025-01-03 07:00 | val_gereolica | (vazio) | NULL + flag; sem imputar |
| B05 | balanco | formato decimal | N, 2025-01-04 08:00 | val_carga | `6705,14699999` | converte para 6705.14699999; flag |
| B06 | balanco | numero invalido | NE, 2025-01-04 09:00 | val_intercambio | `-` | NULL + quarentena |
| B07 | balanco | hora faltante | N, 2025-01-03 05:00 | linha | ausente | lacuna registrada; nao fabrica |
| B08 | balanco | duplicata exata | NE, 2025-01-02 10:00 | linha | repetida | mantem 1; descarta a repetida |
| B09 | balanco | conflito de chave | SE, 2025-01-04 12:00 | val_carga | 43125.513 e 48125.513 | quarentena da chave (2 linhas) |
| B10 | balanco | extremo | SE, 2025-01-05 18:00 | val_carga | 2176462.2 | celula -> NULL; quarentena |
| B11 | balanco | formato data | SIN, 2025-01-06 07:00 | din_instante | `...T07:00:00` | aceita ISO; flag |
| B12 | balanco | categoria caixa | N, 2025-01-06 08:00 | id_subsistema | `n` | upper -> N; flag |
| C13 | curva | categoria caixa/espaco | S, 2025-01-02 03:00 | id_subsistema | ` s ` | trim+upper -> S |
| C14 | curva | categoria caixa/espaco | NE, 2025-01-02 04:00 | nom_subsistema | `nordeste` | -> NORDESTE |
| C15 | curva | numero invalido | SE, 2025-01-03 06:00 | val_...homwmed | `N/A` | NULL + quarentena |
| C16 | curva | celula vazia | SE, 2025-01-03 07:00 | val_...homwmed | (vazio) | NULL + flag |
| C17 | curva | formato decimal | N, 2025-01-04 08:00 | val_...homwmed | `6705,14699999` | converte; flag |
| C18 | curva | hora faltante | N, 2025-01-03 05:00 | linha | ausente | lacuna registrada |
| C19 | curva | duplicata exata | NE, 2025-01-02 10:00 | linha | repetida | mantem 1 |
| C20 | curva | conflito de chave | SE, 2025-01-04 12:00 | val_...homwmed | 2 versoes | quarentena |
| C21 | curva | extremo | SE, 2025-01-05 18:00 | val_...homwmed | 2176462.2 | celula -> NULL |
| C22 | curva | formato data | SE, 2025-01-06 07:00 | din_instante | `...T07:00:00` | aceita ISO |

## Resultados do tratamento (saida real observada)

- `aula2.limpo_balanco` = **838** linhas; `aula2.limpo_curva` = **670**.
- `aula2.quarentena` = **13** registros:
  `conflito_chave` 4, `duplicata_exata` 2, `numero_invalido` 3,
  `celula_vazia` 2, `extremo_quarentena_didatica` 2.
- `aula2.lacunas` (nao imputadas) = 4: a hora N 2025-01-03 05:00 nas duas
  fontes + as chaves SE 2025-01-04 12:00 em quarentena (que viram lacuna).
- Extremos: 2 vao para a quarentena DIDATICA (SE 18:00; criterio de mediana/
  negativo, que NAO prova impossibilidade fisica) e 2 picos termicos do S
  (333.262 e 303.397 MWmed) ficam apenas marcados para revisao (`extremo_revisar`),
  pois estao **presentes no snapshot original** — mantidos, nao removidos.

A politica de extremo gravada em `aula2.quarentena` usa os thresholds REAIS
do 04 (`fator_mediana`, `mult_iqr` lidos de `diagnostico_extremos`); se o aluno
mudar `aluno/parametros_aula2.json`, o texto/politica acompanha.
- `aula2.integrado_limpo` = **838** linhas.

## Impacto (indicadores)

| Medida (SE, val_carga) | referência | naive | tratado |
|---|---|---|---|
| pico | 51471.444 | 2176462.2 | 51471.444 |
| cobertura | 168 | 169 | 166 |
| média | 42559.7869 | 55213.6252 | 42550.5388 |

Leitura: sem tratar, o extremo contamina pico e média. Tratado, o pico real
e recuperado; a cobertura cai 2 pontos porque a chave SE conflitante foi para
quarentena e a celula extrema ficou NULL — o preço da integridade.

## Respostas dos exercicios de parametro

- `mult_iqr = 3`: mais linhas viram "extremo_revisar" (valores presentes no
  snapshot original). Nada e removido automaticamente; a flag apenas sinaliza.
- `fator_mediana = 5`: ainda mais agressivo, mas cargas não variam 5x numa
  semana, então continua capturando só o defeito injetado e alguns extremos
  reais; por isso o default 10 e conservador.
- `imputar = true`: a hora faltante N 05:00 é preenchida pela mediana da mesma
  hora-do-dia, com flag `imputado_hora_do_dia` e registro em `aula2.imputacoes`
  (hipótese + grupo + limite). Nada é imputado sem flag.

## Chaves de integridade

- A integração bruta da aula2 é rejeitada por `03_integrar.py --cenario aula2`
  (exit 2) e registrada em `aula2.integracao_rejeitada` (4 chaves).
- A origem oficial não muda: `sha256` do recorte confere com
  `PROVENIENCIA.json` (teste automatizado).
