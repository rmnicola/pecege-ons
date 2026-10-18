# Design system — páginas de curso

Minimalista e monoespaçado, inspirado na simplicidade de opencode.ai. Uma coluna central emoldurada por linhas finas; seções separadas por divisórias de 1px; nada de sombras, gradientes ou ícones decorativos.

## Tokens (`estilo.css`, `:root`)

| Grupo | Tokens | Uso |
|---|---|---|
| Fundo | `--fundo`, `--fundo-fraco`, `--fundo-fraco-hover`, `--fundo-forte` | página; cartões e hover; blocos de comando |
| Texto | `--texto`, `--texto-fraco`, `--texto-forte`, `--texto-invertido` | corpo; rótulos e datas; títulos e links; texto sobre `--fundo-forte` |
| Linhas | `--borda`, `--borda-fraca` | contorno de cartão; divisórias e moldura |
| Cor | `--destaque`, `--selecao` | acento raro; seleção de texto |
| Tipo | `--fonte` (IBM Plex Mono), `--t-pequeno`, `--t-base`, `--t-titulo`, `--entrelinha` (2) | uma família, três tamanhos, pesos 400/500 |
| Espaço | `--largura` (60rem), `--respiro-x`, `--respiro-y`, `--raio` (4px) | coluna, margens internas das seções |

Modo escuro automático por `prefers-color-scheme`; `data-tema="claro"` no `<html>` força o claro.

## Componentes

- `.moldura` — coluna central com bordas laterais.
- `.topo` — marca à esquerda, navegação em texto à direita.
- `.secao` — bloco com respiro e divisória superior.
- `.rotulo` — metadado pequeno e esmaecido (data, instituição, tipo de arquivo).
- `.aulas` / `.aula` — lista em linhas: data · título e subtítulo · estado.
- `.cartao` — único elemento com contorno: a ação principal da página.
- `.arquivos` — lista de downloads com tipo à direita.
- `.comando` + `.copiar` — bloco de terminal com botão de cópia.
- `.rodape` — créditos e avisos em texto pequeno.

## Regras

- Um só cartão por página: a ação principal.
- Links sublinhados com 1px; sem botões coloridos.
- Títulos em peso 500, nunca negrito pesado.
- Texto corrido com entrelinha 2.
