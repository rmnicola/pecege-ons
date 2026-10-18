# Design system Pecege–ONS

Sistema de apresentações do **Treinamento em Análise de Dados – Analytics**, ministrado por Rodrigo Nicola. Adapta o fluxo didático e as ferramentas do AI for Business à identidade de `Template ONS.pptx`.

## Fonte visual e decisões

O template original tem 7 slides, 16:9, 12192000×6858000 EMU (13⅓×7½ polegadas). A grade HTML é 1600×900. A capa, símbolos, marca ONS, prédio e ondas foram extraídos do próprio arquivo; `assets/proveniencia.json` registra partes e hash do template. Regenere os ativos com `python design-system/tools/extrair-template.py` caso o arquivo oficial seja atualizado.

| Token | Cor | Origem e função |
|---|---|---|
| `--vermelho` | `#F20C3A` | Títulos do slide mestre |
| `--vermelho-marca` | `#CD0028` | Símbolo Pecege; destaque em texto menor |
| `--cinza-texto` | `#60697C` | Corpo e agradecimento |
| `--cinza-escuro` | `#2F2E49` | Ênfase no aviso legal; texto de diagramas |
| `--fundo` | `#F9F9F9` | Fundo efetivo do mestre |
| `--cinza-claro` | `#E8E8E8` | Neutro do tema, apoio a componentes |
| `--branco` | `#FFFFFF` | Texto da capa e áreas de apoio |

As cores de acento azuis/verdes e a Aptos do tema Office **não são a identidade efetiva dos slides**. A identidade é definida pelos estilos e ativos usados no template. O cinza `#90A4AE` aparece em links no original, mas links didáticos usam `#CD0028` para melhor contraste.

### Tipografia e grade

Arial em toda a apresentação; Courier New para código. Linux usa Liberation Sans/Mono como alternativas de métricas compatíveis. Não há download de fontes nem dependência da identidade Inteli.

| Elemento | HTML |
|---|---|
| Título | 64px |
| Frase central | 72px |
| Corpo | 34px |
| Legendas/fontes | 28px |
| Rodapé institucional | 16px |

**Área útil atualizada (13/10/2026):** a caixa de conteúdo padrão agora ocupa de y=80 a y=782 e usa alinhamento superior (`justify-content: flex-start`), em vez de centralização vertical. Títulos ficam mais próximos ao topo e o corpo ganha respiro; layouts que dependem de centralização explícita devem sobrescrever o comportamento no CSS do deck.

Margens horizontais 106px; área útil padrão de y=112 a y=758. Rodapé na faixa inferior. A tipografia do conteúdo é ampliada para apresentação remota, sem alterar a tipografia da marca. A caixa da capa foi ampliada para acomodar títulos de disciplina longos: é uma adaptação de composição, não uma réplica pixel a pixel.

## Estrutura

```text
design-system/
├── assets/img/                    imagens e símbolos oficiais
├── assets/proveniencia.json        rastreabilidade dos ativos
├── css/pecege-ons.css              tokens, componentes e layouts
├── js/deck.js                     navegação, passos, ajuda e rodapé
├── js/codigo.js                   bloco de documentação: highlight, cópia e ajuda
├── tools/deck.mjs                 HTML offline, capturas, QA e PDF opcional
├── tools/extrair-template.py      extração reproduzível dos ativos
├── references/template-visual.md  mapeamento da referência visual para HTML
├── references/decks-inteli.md     ideias de slide dos decks Inteli para portar
├── exemplos/exemplo.html          galeria de composições HTML
└── USO.md / uso.json              registro gerado pelo build
```

Skill: `.agents/skills/apresentacao-pecege-ons/SKILL.md`. Contexto do curso e exigências em seu `references/curso.md`.

## Fluxo

1. Crie `apresentacoes/AAAA-MM-DD-tema/`. Faça uma ideia por slide; a explicação fica na fala do professor, sem notas no HTML.
2. No HTML, ligue `../../design-system/css/pecege-ons.css`. Antes do JS, declare `window.PECEGE_DS = '../../design-system'`; depois carregue `../../design-system/js/deck.js`.
3. Use a galeria para copiar composições. Crie um `id` e `data-modelo` para slides sob medida e mantenha seu CSS no deck.
4. Rode QA incremental e abra as imagens:

```sh
node design-system/tools/deck.mjs apresentacoes/<pasta>/deck.html --slide 3
node design-system/tools/deck.mjs apresentacoes/<pasta>/deck.html --nome aula
```

Build completo: `dist/aula.html` (arquivo único offline), `qa/slide-NN.png`, capturas dos passos, `qa/relatorio.json` e atualização de `USO.md`. Se solicitado, acrescente `--pdf` para exportar `dist/<pasta>.pdf`.

Dependências: Node.js 22+ (WebSocket nativo), Chromium no PATH. Extração de ativos do template: Python 3, biblioteca padrão. Nenhum pacote npm é necessário.

**Formato de apresentação e entrega: exclusivamente HTML**, por decisão do professor. O template enviado serve como referência visual e fonte de ativos; consulte `references/template-visual.md`. O HTML gerado funciona offline. PDF é uma exportação opcional, somente quando solicitada. Os exemplos são uma galeria visual, não aulas completas nem resultados calculados sobre os datasets.

## Pontos de partida e componentes

| Classe | Função |
|---|---|
| `capa sem-numero` | Fotografia vermelha e marcas originais; título e professor |
| `legal sem-numero` | Aviso do template e prédio institucional |
| `agenda` | Lista única que volta a cada parte, em coluna centrada na vertical com o rótulo `.rotulo-agenda`; item atual em bloco preenchido (`.agora`), anteriores suaves (`.passou`); horário e número em `.hora` e `.marcador`; clicar num item abre o slide de agenda correspondente (`data-agora`); `.curta` retoma a lista com letra maior |
| `capitulo-slide ondas` | Abertura de parte da aula, com grafismo do layout 3 |
| `ideia` | Mensagem única em `.frase` |
| `painel` | Comparação em `.colunas` e `.cartao` |
| `fluxo-slide` | Pipeline com `.fluxo`, `.etapa` e `.seta` |
| `codigo-slide` | Trecho curto; prefira `.bloco-codigo`, com arquivo, syntax highlight, cópia e ajuda integrados |
| `imagem` | Figura com legenda e fonte |
| `citacao` | Citação identificada e atribuída |
| `atividade` | Pergunta/dinâmica Wooclap, sem URL ou QR inventado |
| `encerramento sem-numero` | Agradecimento com prédio e símbolo, antes da bibliografia |
| `referencias` | Último slide: links reais e leituras complementares |

O JS insere o rodapé legal e o símbolo Pecege em cada slide de conteúdo. Capa, aviso legal e encerramento usam suas composições originais. Não insira marcas Inteli ou acrescente uma marca ONS improvisada nos slides de conteúdo.

### Blocos de código

Os blocos seguem o padrão do Expressive Code (Starlight), com paleta derivada da identidade (fundo cinza-escuro, destaques em tons do vermelho, secundários em cinzas): `linguagem: 'Python'` gera a moldura de editor, com aba do arquivo e realce de palavras-chave, funções, strings, números, constantes, embutidos, parâmetros e atributos; `linguagem: 'Terminal'` (ou `bash`, `shell`) gera a moldura de terminal, com três pontos, título e realce de comando, opções, strings e variáveis. Todas as cores têm contraste mínimo de 5.5:1 sobre o fundo do código. Carregue `js/codigo.js` antes do script que monta os exemplos e de `js/deck.js`. O build embute tudo no HTML offline. O botão de copiar fica no canto da barra do bloco e copia o texto original, preservando indentação e quebras. Se houver ajuda, o botão `?` também ocupa essa barra.

```html
<div id="codigo-exemplo"></div>
<script src="../../design-system/js/codigo.js"></script>
<script>
  PECEGE_CODIGO.montar(document.getElementById('codigo-exemplo'), {
    arquivo: 'extrair.py',
    linguagem: 'Python',
    codigo: 'import psycopg\nconexao = psycopg.connect()',
    ajudas: [{ inicio: 1, fim: 1, texto: 'Abre a conexão com o banco.' }]
  });
</script>
```

Os intervalos de ajuda são inclusivos, começam em zero e devem estar ordenados, sem sobreposição. Python recebe highlight local; outras linguagens são exibidas como texto. Os tamanhos podem ser ajustados no elemento com `--codigo-fonte`, `--codigo-entrelinha` e `--codigo-padding`; mantenha no mínimo 28px e divida exemplos longos entre slides. O PDF mantém o arquivo e o código completo, ocultando copiar, ajuda e mensagens de confirmação.

## Navegação e passos

→ / L / espaço / Enter avança um passo, depois um slide. ← / H volta. ↓ / J e ↑ / K pulam slides completos. Home/End, F (tela cheia), `#N` na URL. Controles preservam suas teclas; Esc devolve foco à apresentação.

`.passo` + `data-passo="N"` faz entrar; `data-sai="N"` faz sair; `data-passo="0"` começa visível. `data-estado` permite CSS por estado. Conteúdo repetido deve vir de uma única estrutura JS. PDF mostra o estado final; reveja as capturas intermediárias se houver substituições.

Para ajuda em simuladores, marque controles com `data-ajuda` e, se necessário, `data-ajuda-ordem`. Explique siglas em cada balão via `window.notasAjuda`. Durante a ajuda, o elemento em foco fica no retângulo vermelho e o restante do slide é desfocado. A ajuda é removida da impressão.

Trechos de código também podem receber `data-ajuda`. Em slides de código, a ajuda substitui colunas laterais explicativas: deixe o código ocupar a largura. Use `data-ajuda-largura="420"` no slide quando houver uma coluna lateral estreita para os balões (padrão: 560px; limites: 320–900px). `data-ajuda-posicao="direita"` prioriza a coluna lateral antes de tentar acima/abaixo. Botões preservam Enter/espaço para ativação pelo teclado.

Com a ajuda aberta, →/↓ avançam e ←/↑ voltam entre as explicações. Avançar na última fecha a ajuda sem mudar de slide; Esc também fecha. Home/End vão à primeira/última explicação. Os botões possuem hover, cursor de clique e foco visível.

## Verificação

O build acusa área excedida, texto fora da tela, fontes didáticas abaixo de 28px, contraste insuficiente, sobreposição, imagens ausentes, erros de JavaScript e balões fora do slide. Verifica estados finais e intermediários. Rodapé institucional é excluído do limite de tamanho/contagem de palavras; sua geometria e suas imagens continuam verificadas. Objetos externos são exceções controladas, não um modo de contornar a legibilidade.

Avisos: mais de 30 palavras, mais de quatro blocos e layout sob medida sem identificação. `data-max-palavras` admite uma exceção justificada, como bibliografia e aviso legal. Contraste sobre fotografia e sobre gradientes exige revisão visual: o teste CSS usa a cor de fundo, não pixels da imagem.

Abra todas as capturas antes de entregar e confira navegação e interações no HTML autocontido. Não publique a pasta `qa/`.

## Gráficos e dados

Use os dois datasets definidos: [Balanço de Energia](https://dados.ons.org.br/dataset/balanco-energia-subsistema) e [Curva de Carga](https://dados.ons.org.br/dataset/curva-carga). Cada figura leva fonte, período, unidade e identificação de dados simulados quando aplicável. A cor vermelha destaca uma mensagem; séries de contexto usam cinzas, com estilos de linha e rótulos diretos para diferenciá-las. Se forem necessárias mais cores categóricas, solicite uma extensão da paleta em vez de inventar códigos por slide.

Preserve faltantes como faltantes, marque imputações, respeite granularidade e informe revisões/versionamento dos dados. Para a bibliografia final, divida fontes em slides anteriores quando preciso, deixando os links essenciais no último.

## Origem e evolução

`deck.js` e `deck.mjs` derivam das ferramentas locais de `../exec-inteli-ai-for-business/design-system/`, adaptadas para rodapé, layouts e verificações deste curso. CSS, ativos e documentação são próprios. Não foram copiados os históricos de uso, decks ou ativos Inteli. Modelos recorrentes aparecem em `USO.md`; promova componentes com a decisão do professor. Ideias de composição dos decks do professor no Inteli (IA Executiva e M8) estão catalogadas em `references/decks-inteli.md`, com a situação de cada uma.
