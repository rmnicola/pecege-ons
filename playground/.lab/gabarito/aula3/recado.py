"""Gabarito do desafio da aula 3: um recado para cada persona.

    python .lab/gabarito/aula3/recado.py

Grava saida/recado-marina.png, saida/recado-paulo.png e saida/recado-helena.png.
Roda de dentro de playground/ (pasta /work).
"""

import sys

import matplotlib.pyplot as plt

sys.path.insert(0, "aula3")
from fontes import FONTE, dia_tipico, ler_semana, participacao_no_pico, pico_diario  # noqa: E402

cinza, vermelho = "#BFC5CF", "#CD0028"


def br(numero):
    return f"{numero:,.0f}".replace(",", ".")


semana = ler_semana()
tipico = dia_tipico(semana)
picos = pico_diario(semana)
no_pico = participacao_no_pico(semana)
total = semana.sum(axis=1)


# Marina, sala de controle: a que horas a carga do país chega ao pico? Gráfico 2, só o total.
fig, ax = plt.subplots(figsize=(12, 6))
hora = tipico["Total"].idxmax()
ax.plot(tipico.index, tipico["Total"], color=cinza, linewidth=3)
ax.plot(hora, tipico["Total"].max(), "o", color=vermelho, markersize=12)
ax.set_title(f"A carga do país chega ao pico às {hora}h", loc="left", fontsize=20)
ax.spines[["top", "right"]].set_visible(False)
ax.annotate(f"{br(tipico['Total'].max())} MWmed", xy=(hora, tipico["Total"].max()),
            xytext=(0, 14), textcoords="offset points", ha="center", color=vermelho, fontsize=15)
ax.set_xticks(range(0, 24, 2), [f"{h}h" for h in range(0, 24, 2)])
ax.set_ylabel("MWmed (soma dos subsistemas)")
fig.text(0.01, 0.01, FONTE + " Média de cada hora do dia na semana.", fontsize=10, color="gray")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("saida/recado-marina.png", dpi=150)

# Paulo, planejamento: como o pico mudou ao longo da semana? Gráfico 3, com o feriado em destaque.
fig, ax = plt.subplots(figsize=(12, 6))
semana_pt = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
rotulos = [f"{semana_pt[d.weekday()]} {d:%d/%m}" for d in picos.index]
uteis = picos["pico"].iloc[[1, 2, 5, 6]].mean()  # qui 02, sex 03, seg 06 e ter 07/01
queda = (1 - picos["pico"].iloc[0] / uteis) * 100
cores = [vermelho] + [cinza] * (len(picos) - 1)
ax.bar(rotulos, picos["pico"], color=cores)
ax.set_title(f"No feriado de 1º de janeiro, o pico ficou {queda:.0f}% abaixo dos dias úteis",
             loc="left", fontsize=20)
ax.spines[["top", "right"]].set_visible(False)
ax.annotate(f"{br(picos['pico'].iloc[0])} MWmed", xy=(0, picos["pico"].iloc[0]),
            xytext=(0, 6), textcoords="offset points", ha="center", color=vermelho, fontsize=15)
ax.axhline(uteis, color="gray", linestyle="--", linewidth=1)
ax.annotate(f"média dos dias úteis: {br(uteis)} MWmed", xy=(-0.4, uteis), xytext=(0, 6),
            textcoords="offset points", ha="left", color="gray", fontsize=12)
ax.set_ylabel("Maior carga horária do dia, MWmed")
fig.text(0.01, 0.01, FONTE + " Soma dos quatro subsistemas.", fontsize=10, color="gray")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("saida/recado-paulo.png", dpi=150)

# Helena, diretoria: que subsistema pesa mais no pico do país? Gráfico 4, de pizza para barras.
fig, ax = plt.subplots(figsize=(12, 6))
ordem = no_pico.sort_values()
barras = ax.barh(ordem.index, ordem.values, color=[vermelho if s == "SE" else cinza for s in ordem.index])
ax.bar_label(barras, [f"{v:.0f}%" for v in ordem.values], padding=6, fontsize=15)
ax.set_title(f"No pico do país, o SE respondeu por {no_pico['SE']:.0f}% da carga", loc="left", fontsize=20)
ax.spines[["top", "right", "bottom"]].set_visible(False)
ax.set_xticks([])
ax.tick_params(axis="y", labelsize=15)
fig.text(0.01, 0.01, FONTE + f" Hora de maior carga da semana: {total.idxmax():%d/%m, %Hh}.",
         fontsize=10, color="gray")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("saida/recado-helena.png", dpi=150)

print("Gravados saida/recado-marina.png, saida/recado-paulo.png e saida/recado-helena.png")
