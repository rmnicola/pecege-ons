# Pecege–ONS

Para criar, editar ou revisar apresentações deste curso, leia e siga:

1. `.claude/skills/apresentacao-pecege-ons/SKILL.md`
2. `design-system/README.md`

As apresentações são exclusivamente em HTML autocontido e interativo. `Template ONS.pptx` é apenas referência visual e fonte de ativos; preserve esse arquivo. Leia `design-system/references/template-visual.md` para o mapeamento da identidade. Exporte PDF somente quando solicitado.

As aulas e os prazos estão em `.claude/skills/apresentacao-pecege-ons/references/curso.md`. Os datasets definidos são Balanço de Energia nos Subsistemas e Curva de Carga Horária do Portal de Dados Abertos do ONS.

Apresentações devem ter fontes explícitas e referências no último slide. Não escreva notas do professor (`<aside class="notas">`): o professor não as usa. Verifique dados e dicionários antes de atribuir conclusões às bases oficiais. Siga a identidade Pecege–ONS documentada neste projeto.

Este projeto é o repositório público github.com/rmnicola/pecege-ons; cada push em `main` publica o site (https://rmnicola.github.io/pecege-ons/). Siga o fluxo do `README.md`: aulas em andamento ficam com `"rascunho": true` em `curso.json`; mostre a prévia (`python3 tools/gerar_site.py --previa`) e só faça commit/push quando o professor pedir. Nunca adicione arquivos privados listados no `.gitignore` (e-mails, template, capturas de QA).
