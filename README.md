# Pecege · ONS — Treinamento em Análise de Dados

Materiais das aulas de Rodrigo Nicola: apresentações, preparação do ambiente e laboratório.

**Site:** https://rmnicola.github.io/pecege-ons/

## Estrutura

```
curso.json              fonte única: dados do curso e lista de aulas
aulas/<slug>/           arquivos publicados de cada aula (apresentação, PDFs)
site/estilo.css         design system das páginas (ver site/DESIGN.md)
tools/gerar_site.py     gera _site/ a partir de curso.json (só biblioteca padrão)
.github/workflows/      publica no GitHub Pages a cada push em main
```

## Adicionar uma aula

1. Crie `aulas/<AAAA-MM-DD-tema>/` com os arquivos da aula.
2. Em `curso.json`, preencha a aula: `apresentacao` (arquivo HTML), `antes` (arquivos para baixar) e `laboratorio` (mostra o comando de clone).
3. Uma aula sem `apresentacao` nem `antes` aparece como "em breve".
4. Faça push em `main`: o site é publicado automaticamente.

Para ver localmente: `python tools/gerar_site.py` e abra `_site/index.html`.

## Reaproveitar em outra matéria

Copie `site/`, `tools/` e `.github/` para o repositório novo, escreva o `curso.json` e ative **Settings → Pages → Source: GitHub Actions**.
