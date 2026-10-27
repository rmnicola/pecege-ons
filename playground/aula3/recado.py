"""Desafio: do gráfico ao recado.

Escolha uma persona e o gráfico de aula3/exploracao.ipynb que responde à pergunta dela.
Transforme esse gráfico no recado para ela. A imagem sai em saida/recado.png.

Rode quantas vezes quiser:

    python aula3/recado.py

Documentação do matplotlib: https://matplotlib.org/stable/api/
"""

import matplotlib.pyplot as plt

from fontes import FONTE, dia_tipico, ler_semana, participacao_no_pico, pico_diario

# As personas (as fichas estão no slide):
#   Marina, coordenação da sala de controle: a que horas a carga do país chega ao pico?
#   Paulo, planejamento: como o pico de carga mudou ao longo da semana?
#   Helena, diretoria: que subsistema pesa mais no pico do país?

grafico = 1  # troque pelo número do gráfico do notebook (1 a 5)

semana = ler_semana()
cinza, vermelho = "#BFC5CF", "#CD0028"
fig, ax = plt.subplots(figsize=(12, 6))

# O gráfico escolhido, do jeito que está no notebook. Mexa só no bloco do seu gráfico.
# Para destacar o que importa (passo 3), troque as cores aqui: cinza no contexto, vermelho no recado.
#     plot  https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html
#     bar   https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.bar.html
#     barh  https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.barh.html
#     hist  https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.hist.html

if grafico == 1:  # A semana hora a hora
    for subsistema in semana.columns:
        ax.plot(semana.index, semana[subsistema], label=subsistema)
    ax.legend()

elif grafico == 2:  # O dia típico
    tabela = dia_tipico(semana)
    for coluna in tabela.columns:
        ax.plot(tabela.index, tabela[coluna], label=coluna)
    ax.legend()

elif grafico == 3:  # O pico de cada dia
    tabela = pico_diario(semana)
    rotulos = [f"{dia:%d/%m}" for dia in tabela.index]
    barras = ax.bar(rotulos, tabela["pico"])

elif grafico == 4:  # Quem pesa no pico
    tabela = participacao_no_pico(semana)
    ax.pie(tabela, labels=tabela.index)

elif grafico == 5:  # Como a carga total se distribui
    total = semana.sum(axis=1)
    ax.hist(total)


# Passo 1. Título que diz a conclusão
# A resposta à pergunta da persona, como "O SE é mais da metade da carga", e não o assunto.
#     set_title  https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_title.html

titulo = ""  # troque
ax.set_title(titulo, loc="left", fontsize=18)


# Passo 2. Tirar o que distrai
# Molduras, legenda, séries que não ajudam a responder (apague-as no bloco do gráfico).
#     spines  https://matplotlib.org/stable/api/spines_api.html
# Exemplos:
#     ax.spines[["top", "right"]].set_visible(False)
#     ax.get_legend().remove()


# Passo 3. Destacar só o que importa
# Troque as cores no bloco do seu gráfico. Exemplos:
#     ax.plot(x, y, color=cinza)
#     ax.plot(x, y, color=vermelho, linewidth=3)
#     barras = ax.bar(x, y, color=cinza); barras[0].set_color(vermelho)


# Passo 4. Anotar a evidência, com unidade
#     annotate    https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.annotate.html
#     set_ylabel  https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_ylabel.html
# Exemplos:
#     ax.annotate("86.834 MWmed", xy=(20, 86834), xytext=(0, 10), textcoords="offset points", color=vermelho)
#     ax.set_ylabel("MWmed")


# Passo 5. Fonte e limites
# FONTE já traz a base, o período e a data de extração. Acrescente o que limita a leitura.

nota = FONTE  # troque
fig.text(0.01, 0.01, nota, fontsize=10, color="gray")


# Passo 6. Gravar a imagem: é ela que vai para a persona
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("saida/recado.png", dpi=150)
print("Recado gravado em saida/recado.png")
