# Pecege–ONS · Treinamento em Análise de Dados — Analytics

Materiais das aulas de Rodrigo Nicola: apresentações, preparação do ambiente e laboratório.

**Site:** https://rmnicola.github.io/pecege-ons/ — publicado automaticamente a cada push em `main`.

## Estrutura

```
curso.json                    fonte única do site: curso e aulas
apresentacoes/<data-tema>/    deck.html (fonte), dist/index.html (build), preparacao.json (opcional)
playground/                   laboratório: aula1/, aula2/, saida/ e preparar.sh; o interno fica em .lab/
design-system/                identidade Pecege–ONS dos slides e ferramenta de build
site/                         design system das páginas do site (ver site/DESIGN.md)
tools/gerar_site.py           gera _site/ a partir de curso.json
.agents/skills/               skills (Claude Code, Codex, OpenCode, Gemini); .claude/skills é link para cá
```

## Fluxo de trabalho

1. Trabalhe na aula em `apresentacoes/<data-tema>/` e gere o deck:
   `node design-system/tools/deck.mjs apresentacoes/<data-tema>/deck.html`
2. Registre a aula em `curso.json` com `"pasta"`, `"apresentacao": "dist/index.html"` e, enquanto estiver em andamento, `"rascunho": true`.
3. Veja a prévia local, com rascunhos: `python3 tools/gerar_site.py --previa` e abra http://localhost:8000
4. Para publicar, retire `"rascunho"` da aula, faça commit e push em `main`.

Aulas com `"rascunho": true` ficam fora do site publicado, mesmo que seus arquivos estejam no repositório. A senha das páginas (hash em `senha_sha256`) é só uma barreira visual: o repositório é público.

Em `curso.json`, cada aula aceita `proposito` e `objetivos` (objetivos de aprendizagem), `antes` (links ou arquivos para antes da aula) e `laboratorio` (mostra o comando de clone). Um `preparacao.json` na pasta da aula vira a página de passo a passo.

## Referências internas

- Skill de apresentações: [`.agents/skills/apresentacao-pecege-ons/SKILL.md`](.agents/skills/apresentacao-pecege-ons/SKILL.md)
- Design system dos slides: [`design-system/README.md`](design-system/README.md) · galeria: `node design-system/tools/deck.mjs design-system/exemplos/exemplo.html`
- Playground: os alunos rodam `./preparar.sh` no começo de cada aula. Ele faz `git pull`, apaga o laboratório anterior (contêineres e volumes) e sobe tudo do zero. O código roda no contêiner `playground`, onde o aluno entra pelo VS Code (Dev Containers → Attach to Running Container). O gabarito fica em `playground/.lab/gabarito/`.
- Contexto e cronograma: [`.agents/skills/apresentacao-pecege-ons/references/curso.md`](.agents/skills/apresentacao-pecege-ons/references/curso.md)

## Reaproveitar em outra matéria

Copie `site/`, `tools/` e `.github/` para o repositório novo, escreva o `curso.json` e ative **Settings → Pages → Source: GitHub Actions**.
