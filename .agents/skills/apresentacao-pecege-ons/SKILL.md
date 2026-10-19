---
name: apresentacao-pecege-ons
description: "Cria, edita e revisa apresentações HTML interativas de arquivo único para slides, aulas e workshops do curso Treinamento em Análise de Dados – Analytics, Pecege–ONS. Use sempre que o pedido envolver apresentações deste curso. Aplica a identidade visual extraída do template enviado, revisão visual e exemplos com os datasets de Balanço de Energia e Curva de Carga do ONS. Para registrar a aula no site, mostrar a prévia ou publicar, use também a skill curso-site."
---

# Apresentações Pecege–ONS

Leia `design-system/README.md` antes de criar o primeiro slide e `references/curso.md` para escopo, datas e datasets. Os caminhos são relativos à raiz deste projeto.

Esta adaptação deriva de `../exec-inteli-ai-for-business/.claude/skills/apresentacao-inteli/SKILL.md`. Mantém o fluxo didático, a navegação, os passos e a revisão; a identidade vem exclusivamente de `Template ONS.pptx`.

## Quem conduz e o que aparece

- O professor guia o conteúdo. Quando faltar direção, proponha uma ou duas opções curtas. Se ele pedir um deck completo, execute o escopo solicitado; para trabalho iterativo, avance um slide ou pequeno grupo por vez e peça feedback.
- Uma mensagem por slide. Em cerca de 30 segundos a turma deve consumir a tela e voltar à fala: aproximadamente 30 palavras, até quatro blocos, sem parágrafos longos. Explicações, comandos adicionais e respostas ficam na fala do professor; não escreva notas do professor nos slides.
- O professor prefere uma sequência curta e lógica de referências, diagramas e estruturas que sustentem a explicação do problema. Evite frases de efeito, máximas óbvias, slides motivacionais e divisórias redundantes. Não há meta de quantidade de slides: cada um precisa servir à condução.
- Nas aulas de ETL, a primeira parte explica como enfrentar o problema (fontes heterogêneas na aula1; dados de qualidade desconhecida e critérios de uso na aula2). A segunda parte apresenta ambiente, enunciado, tarefas e critérios de entrega; quando o professor decidir, cada desafio é seguido do slide de solução. No slide de ambiente, só `./preparar.sh` dentro de `pecege-ons/playground`: o script atualiza o material e refaz o laboratório do zero. A instalação inicial fica na página de preparação da aula 1 (`preparacao.json`, skill curso-site). O aluno trabalha dentro do contêiner `playground` (VS Code: Dev Containers → Attach to Running Container), como numa máquina local: comandos nos slides são `python aula1/...` e `psql`, nunca `docker compose run`; não discuta contêineres em aula. Caminhos citados são os da pasta do aluno (`aula1/`, `aula2/`, `saida/`); o gabarito fica escondido em `playground/.lab/` e não é citado.
- Introduza termos dentro do exemplo ou diagrama em que fazem sentido, com `.rotulo-termo`; evite glossários isolados.
- Não invente resultados, falhas nos dados oficiais, unidades, chaves, definições, datas de extração ou fontes. Identifique exemplos sintéticos e alterações didáticas. Consulte os dicionários antes de integrar as duas bases.

## Identidade única

- Use Arial e a paleta de `design-system/css/pecege-ons.css`; para código, Courier New. Arial pode ser substituída por Liberation Sans no Linux, com métricas compatíveis. Não use fontes, logos, molduras ou grafismos Inteli.
- Abra com a capa fotográfica oficial (slide 1 do template de referência). Preserve a imagem e os logos, sem recolorir, deformar ou desenhar uma marca nova.
- Preserve o aviso legal do slide 2 e o rodapé dos layouts de conteúdo. O rodapé é institucional e pode ter tamanho menor que o texto didático.
- Conteúdo: fundo `#F9F9F9`, títulos `#F20C3A`, corpo `#60697C`; `#CD0028` para destaque em texto menor. Use `ondas` como variante do layout 3, com a inversão vertical do original.
- Reserve a parte inferior para o rodapé. Fora de objetos, mantenha conteúdo didático em pelo menos 28px no HTML; prefira 34–40px no corpo e 64px nos títulos.
- Coloque o agradecimento antes das referências: o último slide deve conter links ou referências das leituras complementares, conforme o e-mail do Pecege.
- Não acrescente wifi, pesquisa ou QR code do Inteli. Para Wooclap, só gere QR code quando houver URL real fornecida ou confirmada.

## Formatos e ferramentas

O professor definiu **HTML como único formato de apresentação e entrega**. `Template ONS.pptx` serve apenas como referência visual e fonte de ativos. Produza um HTML autocontido, offline, com navegação e interações. PDF só deve ser exportado se solicitado explicitamente.

### HTML interativo

1. Crie `apresentacoes/AAAA-MM-DD-tema/deck.html`. Use `design-system/exemplos/exemplo.html` como referência e ajuste os caminhos para `../../design-system/`.
2. Ligue `css/pecege-ons.css` e `js/deck.js`. Declare `window.PECEGE_DS` com o caminho relativo do design system antes do JS para que os rodapés usem o ativo correto.
3. Use pontos de partida apenas quando servirem à ideia: `capa`, `legal`, `agenda`, `capitulo-slide`, `ideia`, `painel`, `fluxo-slide`, `codigo-slide`, `imagem`, `citacao`, `atividade`, `encerramento`, `referencias`.
4. Para um layout sob medida, dê ao slide `id` e `data-modelo`, e escreva o CSS no deck com seletores pelo `#id`. Não altere o sistema para resolver um único slide.
5. Conteúdo repetido vem de uma fonte única (agenda, marcos, diagramas). Use `.passo`, `data-passo` e `data-sai` para revelação e substituição; `data-estado` permite mudar estilos por estado. PDF mostra o estado final.
6. Centralize verticalmente com flexbox. Evite `top:50%` + `translateY(-50%)` em conteúdo: pode quebrar a paginação do PDF.
7. Para reproduzir um terminal ou página externa, use `.objeto` com aparência original, mas sem esconder conteúdo didático em fonte pequena. Dê contexto e destaque legível.
8. Simuladores usam controles reais, estado compartilhado quando necessário e casas decimais fixas. Para vários controles, use `data-ajuda` e explique siglas nos balões via `window.notasAjuda`.

## Verificação e entrega

1. Execute `node design-system/tools/deck.mjs <deck.html> --slide N` durante a edição. Corrija erros e trate avisos.
2. Abra `qa/slide-NN.png` e os estados `qa/slide-NN-passo-K.png`: revise alinhamento, respiro, hierarquia, rodapé, contraste, legibilidade e consistência das unidades.
3. Para revisão incremental, mostre o slide ao professor e diga em uma linha sua função e composição.
4. Ao terminar, rode o build completo. Ele gera HTML autocontido offline, capturas e `qa/relatorio.json`. Use `--pdf` apenas se uma exportação PDF for solicitada: sai uma página por slide e uma por conteúdo que um passo substitui.
5. O arquivo publicado é `dist/index.html`. Confirme funcionamento offline, navegação, interações e referências.
6. Registre ou atualize a aula em `curso.json` como rascunho e mostre a prévia do site, seguindo a skill curso-site. Commit e push publicam: só faça quando o professor pedir. `qa/`, PDFs e dados pessoais de participantes nunca entram no repositório.

## Evolução

Use o mesmo `data-modelo` para composições semelhantes. Um modelo repetido pode virar componente reutilizável, mediante decisão do professor. Atualize CSS, `LAYOUTS` da ferramenta e README juntos. Este sistema tem identidade própria e não precisa ser sincronizado com as cópias Inteli.
