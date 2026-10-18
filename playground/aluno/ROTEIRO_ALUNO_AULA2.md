# Aula 2 — roteiro operacional do aluno

Use o ambiente da aula1, previamente preparado. A cópia `laboratorio.*` contém alterações didáticas para investigação; os dados oficiais estão preservados. Não refaça o setup com `00` sem necessidade de reiniciar o laboratório.

## 1. Extrair as entradas

```sh
docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula2
docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula2
```

As staging `aula2.stg_*` preservam o conteúdo recebido como texto. Registre fontes e inspecione entradas antes de propor transformações.

## 2. Verificar se é possível integrar

```sh
docker compose run --rm etl python scripts/03_integrar.py --cenario aula2
```

A rejeição com código de saída2 faz parte do exercício. Leia a causa e consulte `aula2.integracao_rejeitada`; identifique o requisito violado e o que investigar.

## 3. Diagnosticar

```sh
docker compose run --rm etl python scripts/04_diagnosticar.py
docker compose exec destino psql -U ons_lab -d analytics
```

Escreva as consultas de `aluno/exercicios_aula2.sql`. Examine `aula2.diagnostico_*`, distinguindo ausências, cobertura, conflitos, formatos e valores suspeitos. Normalizar a chave ajuda a reconhecer conflitos sem sobrescrever o bruto.

## 4. Propor e executar políticas

Antes de tratar, registre problema, evidência, regra, ação e efeito esperado. Em seguida:

```sh
docker compose run --rm etl python scripts/05_tratar.py
```

Inspecione `aula2.limpo_*`, `aula2.quarentena`, `aula2.lacunas` e flags. Compare sua proposta com a implementação. Esse script integra a saída tratada após verificar unicidade; não repetir `03` como se ele integrasse as tabelas limpas.

### Experimento com parâmetros

Edite `aluno/parametros_aula2.json`, um parâmetro por vez. Registre hipótese e compare efeitos:

- `mult_iqr` e `fator_mediana`: reexecute04e05; investigue valores sinalizados ou na quarentena didática. Justifique o critério: limiar estatístico não prova impossibilidade física.
- `imputar`: extensão opcional. Reexecute05; a implementação preenche lacunas de registro pela mediana da mesma hora, não células existentes. Registre hipótese, grupo, flags e limite de valor(min/max), que não é limite de comprimento da lacuna.

Restaure os parâmetros iniciais ao terminar e mantenha o arquivo utilizado como evidência.

## 5. Avaliar a saída

```sh
docker compose run --rm etl python scripts/06_avaliar.py
```

Compare cenários em `aula2.avaliacao_indicadores`, especificando medida, grupo, unidade e denominador. A referência limpa é recurso didático de avaliação, não uma maneira automática de conhecer os valores corretos em produção.

## Entrega

Consultas, parâmetros e tabela de regras com evidências, efeitos e limitações. Explique quais dados podem ser publicados, exigem uso restrito ou devem ser rejeitados/investigados. Não há resultados de gabarito neste roteiro.
