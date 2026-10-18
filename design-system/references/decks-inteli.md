# Decks Inteli — ideias de slide para portar

Os decks do professor no Inteli são a referência de composição deste design system. As ideias abaixo são reescritas na identidade Pecege–ONS (Arial, paleta do `pecege-ons.css`, sem fontes, logos, roxos, corais ou grafismos Inteli; sem wifi, pesquisa ou QR do Inteli).

Fontes (nesta máquina):

- **Exec · AI for Business** — `../exec-inteli-ai-for-business/apresentacoes/2026-10-03-essencial-na-pratica/deck.html`: um dia de curso, com agenda recorrente, objetos de empresa e atividades cronometradas.
- **M8 · Navegação autônoma** — `../m8-inteli-navegacao/apresentacoes/2026-10-14-apresentacao-do-modulo/deck.html`: apresentação do módulo, com agenda curta entre blocos, fluxo com detalhe por passo e materiais de referência.

| Ideia | Origem | O que faz | Uso no Pecege–ONS | Situação |
|---|---|---|---|---|
| **Agenda recorrente** | Exec `#agenda-1` e demais `.agenda`; M8 `.agenda.curta` | A mesma lista volta ao longo do dia: item atual destacado, anteriores suaves; clicar num item abre o slide daquele item; horário no marcador; `.curta` retoma com letra maior | `agenda` do design system: `.marcador`, `.hora`, `.rotulo-agenda` e `.curta`; usada na aula 1 com horários do roteiro | **Portada** (14/10/2026) |
| **Fluxo com detalhe por passo** | M8 `.fluxo-detalhes` (`#revisao`, `#validar-desafio`); parente: Exec `.caminho` (`#fluxo-reuniao`) | O fluxo inteiro fica visível; avançar destaca uma etapa e mostra o texto dela abaixo, uma por vez | Esquema de etapa + detalhe com `data-estado`; no slide CRISP-DM da aula 1, com CSS local | Em uso na aula 1; vira componente se repetir |
| **Objetos externos com destaque progressivo** | Exec `#artigo-turing`, `#corpo-*`, `#jornal-1958`, `#builder-log-*`, `#caso-2` | Representar o material como ele é (página de artigo, jornal, ficha, anotações) e revelar o que importa por passo, desfocando o resto | Seção "O mundo real": dicionário do ONS, CSV congelado, roteiro da atividade; dentro do `.objeto` vale a aparência do original | Candidata |
| **Linha do tempo que acumula** | Exec `.linha-do-tempo`; M8 `.linha-sprints` | A mesma linha reaparece depois de cada bloco, com os marcos preenchidos até o momento; marcos vêm de uma fonte única | Cronologia de um processo (extração, revisões) ou do próprio curso | Candidata |
| **Atividade com timer** | Exec `#revisao-cruzada` | Contagem regressiva com iniciar/zerar (tecla T), visível só no HTML | Blocos práticos da segunda parte, que já têm tempo definido no roteiro | Candidata |
| **Painel em passos** | M8 `#nota-individual` | Uma fórmula aparece e se abre em partes (barra de pesos) conforme avança | Métricas com composição (completude, cobertura, taxa de rejeição) | Candidata |
| **Calendário** | M8 `#semana-1`, `#prazos` | Dias da semana em tabela, ou colunas com cartões de entrega e prazos | Cronograma do curso e prazos de entrega das aulas | Candidata |
| **Estante** | M8 `.estante` | Capas de livros lado a lado; a principal maior; cada capa é um link | Slide de leituras, quando a capa ajudar a reconhecer a referência | Candidata |
| **Cena ilustrada** | M8 `#estacao`, `#totem`, `#robo`; Exec `#caso-1`, `#jogo-da-imitacao` | Figuras e falas para dramatizar o problema antes de nomeá-lo | Avaliar caso a caso: o curso usa mais diagramas que cenas | Candidata |

## Como portar

1. Reescreva na identidade Pecege–ONS: tokens de `pecege-ons.css`, Arial, nada abaixo de 28px, uma ideia por slide.
2. Reaproveite o mecanismo de passos (`data-passo`, `data-sai`, `data-estado`) em vez de criar animações novas.
3. Ao promover a ponto de partida, atualize juntos: CSS, `exemplos/exemplo.html`, README e a lista `LAYOUTS` do `tools/deck.mjs`.
4. Registre a origem na nota do slide (como na aula 1) e atualize a coluna "Situação" desta tabela.
