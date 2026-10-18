---
name: curso-site
description: "Mantém o site do curso Pecege–ONS publicado no GitHub Pages a partir deste repositório: registra aulas em curso.json, marca rascunhos, escreve páginas de preparação do ambiente (preparacao.json), ajusta o estilo do site com as regras de contraste, mostra a prévia local e publica com commit e push quando o professor pedir. Use sempre que o pedido envolver o site, a página de uma aula, materiais para os alunos baixarem, preparação do ambiente, prévia, publicação, commit ou push deste projeto."
---

# Site do curso

Este projeto é o repositório público https://github.com/rmnicola/pecege-ons. Cada push em `main` publica https://rmnicola.github.io/pecege-ons/ pelo workflow `.github/workflows/pages.yml`, que verifica o contraste e roda `tools/gerar_site.py`.

## Regra principal: discutir antes de publicar

Commit e push publicam. Trabalhe localmente, mostre a prévia e só faça commit/push quando o professor pedir. Na dúvida, pergunte.

```sh
python3 tools/gerar_site.py --previa     # inclui rascunhos; serve em http://localhost:8000
```

Rode a prévia em segundo plano e não inicie um segundo servidor: os dois disputam `_site/`. Senha das páginas: `pecege-ons`.

## Onde fica cada coisa

| Caminho | Papel |
|---|---|
| `curso.json` | fonte única do site: dados do curso, hash da senha e lista de aulas |
| `apresentacoes/<AAAA-MM-DD-tema>/` | `deck.html` (fonte), `dist/index.html` (build publicado), `preparacao.json` |
| `site/estilo.css`, `site/DESIGN.md` | design system das páginas: tokens, componentes, regras de contraste |
| `tools/gerar_site.py` | gera `_site/`: índice, página de cada aula, preparação, tela de senha |
| `tools/verificar_contraste.py` | regras C1–C4 e T1; falha bloqueia a publicação |
| `playground/` | laboratório que os alunos clonam (`gabarito/` é público, por decisão do professor) |

## Registrar uma aula

Em `curso.json`, cada aula tem:

| Campo | Uso |
|---|---|
| `slug` | URL: `aulas/<slug>/`. Não mude depois de divulgado |
| `pasta` | pasta da aula em `apresentacoes/` |
| `rascunho` | `true` enquanto estiver em andamento: fica fora do site publicado, aparece na prévia |
| `data`, `horario`, `titulo`, `subtitulo` | textos da lista e da página |
| `proposito`, `objetivos` | frase de propósito e lista de objetivos de aprendizagem da página da aula (o professor prefere objetivos a um resumo) |
| `apresentacao` | arquivo relativo à pasta, normalmente `dist/index.html`; vira `apresentacao.html` |
| `antes` | lista de `{rotulo, tipo, link}` (página) ou `{rotulo, tipo, arquivo}` (arquivo da pasta, baixado) |
| `laboratorio` | `true` mostra o comando de clone; o professor preferiu não usar (o "Antes da aula" já leva ao passo a passo) |

Aula sem `pasta` aparece como "em breve". O CI não roda o build dos decks (precisa de Chromium): `dist/index.html` precisa estar atualizado e commitado.

## Página de preparação

`apresentacoes/<pasta>/preparacao.json` vira `aulas/<slug>/preparacao/`. O professor prefere página com comandos copiáveis a PDF.

```jsonc
{
  "titulo": "Preparação do ambiente",
  "resumo": "…",                       // aceita `código`, **forte**, *ênfase*
  "passos": [
    {
      "titulo": "…",
      "texto": ["…"],                  // antes do comando; 2+ itens viram lista numerada
      "comandos": "linha 1\nlinha 2",  // bloco de terminal com realce e botão copiar
      "saida": "…",                    // moldura "Saída esperada"
      "depois": ["…"],
      "aviso": "…"
    }
  ],
  "problemas": [["mensagem", "o que fazer"]],
  "fechamento": "…",
  "dia_da_aula": "comandos"
}
```

Prefira um script único e idempotente no playground (como `./preparar.sh`) a uma sequência longa de comandos. Antes de publicar instruções, teste-as do zero com um clone real e um projeto Docker isolado (`COMPOSE_PROJECT_NAME=<teste>` ou `-p <teste>`; o compose fixa `name: pecege-ons-etl`, e `down -v` sem isolamento apaga os volumes reais).

## Estilo do site

Minimalista e monoespaçado, inspirado em opencode.ai; blocos de código no estilo Starlight. Leia `site/DESIGN.md` antes de mexer. Toda cor nova vira token em `site/estilo.css`, ganha um par em `PARES` no verificador e deve passar em:

```sh
python3 tools/verificar_contraste.py
```

Confira as páginas na prévia em 1280px e 390px. Para capturar uma página atrás da senha, digite `pecege-ons` no campo `#portao-senha` antes da captura.

## Publicar (somente quando o professor pedir)

1. Retire `"rascunho"` da aula, se for o caso, e confira a prévia.
2. `python3 tools/verificar_contraste.py` e `python3 tools/gerar_site.py` sem erros.
3. `git status`: confirme que nada privado entra (e-mails, `Template ONS.pptx`, `qa/`, PDFs, `revisao-*.md`, `.env` são ignorados). Use `git add` com caminhos explícitos quando houver alterações fora do escopo.
4. Commit em português, descrevendo o que muda para quem usa o site, com a linha de coautoria da sessão. Autor: Rodrigo Nicola.
5. `git push origin main` e confira o workflow (API pública: `https://api.github.com/repos/rmnicola/pecege-ons/actions/runs`).

## Senha

Só o hash SHA-256 fica em `curso.json` (`senha_sha256`); a comparação ignora maiúsculas e minúsculas, então gere o hash da senha em minúsculas. A tela é uma barreira visual: o repositório e os links diretos de arquivos continuam públicos. Diga isso ao professor sempre que o assunto for privacidade.
