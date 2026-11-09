"""Los tres gráficos del estudio, en español o en inglés.

- Pedido por modelo: el escenario base, con el rango entre conservador y optimista, y las ventas
  del competidor de referencia al lado.
- Embudo de la encuesta: cuántas respuestas caen por cada motivo y cuántas quedan.
- Test A/B: la proporción que elige el frente A, con su intervalo, en total y por edad.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

TINTA, SUAVE, ACENTO, LINEA, FONDO, VERDE = ("#16161a", "#55555f", "#9a3412", "#dededa",
                                             "#fbfbf9", "#2f6f73")
plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "axes.edgecolor": LINEA, "axes.labelcolor": SUAVE, "xtick.color": SUAVE,
    "ytick.color": SUAVE, "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
})

TEXTOS = {
    "es": {
        "t_pedido": "Ventas al mes por modelo: tres escenarios de cuota y el competidor de referencia",
        "x_pedido": "unidades al mes",
        "base": "escenario base (barra: de conservador a optimista)",
        "competidor": "competidor de referencia en el marketplace",
        "revisar": "revisar",
        "t_embudo": "De las respuestas recibidas a las que valen",
        "recibidas": "Recibidas", "validas": "Válidas",
        "motivos": {"duplicado": "Duplicadas", "demasiado rápida": "Demasiado rápidas",
                    "falla el control": "Fallan el control", "en línea recta": "En línea recta",
                    "otro idioma": "En otro idioma"},
        "t_ab": "Eligen el frente A: proporción e intervalo de confianza del 95 %",
        "x_ab": "% que elige el frente A",
        "grupos": {"Total": "Total", "menos de 45": "Menos de 45", "45 a 64": "45 a 64",
                   "65 o más": "65 o más"},
        "empate": "50 %: empate",
    },
    "en": {
        "t_pedido": "Monthly sales by model: three share scenarios and the reference competitor",
        "x_pedido": "units a month",
        "base": "base scenario (bar: conservative to optimistic)",
        "competidor": "reference competitor on the marketplace",
        "revisar": "check",
        "t_embudo": "From responses received to responses that count",
        "recibidas": "Received", "validas": "Valid",
        "motivos": {"duplicado": "Duplicates", "demasiado rápida": "Too fast",
                    "falla el control": "Failed attention check",
                    "en línea recta": "Straight-lined", "otro idioma": "Not in Spanish"},
        "t_ab": "Choose front A: share and 95% confidence interval",
        "x_ab": "% choosing front A",
        "grupos": {"Total": "Total", "menos de 45": "Under 45", "45 a 64": "45 to 64",
                   "65 o más": "65 and over"},
        "empate": "50%: a tie",
    },
}


def _titulo(ax, texto: str) -> None:
    ax.set_title(texto, loc="left", fontsize=14, color=TINTA, weight="bold", pad=14)


def pedido(est: pd.DataFrame, idioma: str = "es"):
    t = TEXTOS[idioma]
    e = est.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 0.9 * len(e) + 1.8))
    for i, f in e.iterrows():
        ax.plot([f["ventas_mes_conservador"], f["ventas_mes_optimista"]], [i, i], color=LINEA,
                lw=8, solid_capstyle="round", zorder=1)
        color = ACENTO if f["revisar"] else VERDE
        ax.scatter(f["ventas_mes_base"], i, s=110, color=color, zorder=3)
        ax.scatter(f["ventas_competidor_mes"], i, marker="|", s=420, color=TINTA, zorder=2)
        txt = f"{f['ventas_mes_base']:.0f}"
        if f["revisar"]:
            txt += f"  · {t['revisar']}"
        ax.annotate(txt, (f["ventas_mes_base"], i), xytext=(0, 11), textcoords="offset points",
                    ha="center", fontsize=10, color=color)
    ax.set_yticks(range(len(e)))
    ax.set_yticklabels(e["modelo"], fontsize=11)
    ax.set_xscale("log")
    ax.set_xlabel(t["x_pedido"] + " (log)")
    ax.scatter([], [], s=110, color=VERDE, label=t["base"])
    ax.scatter([], [], marker="|", s=200, color=TINTA, label=t["competidor"])
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _titulo(ax, t["t_pedido"])
    fig.tight_layout()
    return fig


def embudo(limpias: pd.DataFrame, idioma: str = "es"):
    t = TEXTOS[idioma]
    cuentas = limpias["motivo_descarte"].value_counts()
    filas = [(t["recibidas"], len(limpias), SUAVE)]
    filas += [(t["motivos"][m], -int(cuentas.get(m, 0)), ACENTO) for m in t["motivos"]]
    filas += [(t["validas"], int(limpias["motivo_descarte"].isna().sum()), VERDE)]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    restante = len(limpias)
    for i, (nombre, valor, color) in enumerate(filas):
        if i == 0 or i == len(filas) - 1:
            ax.barh(i, valor, color=color, height=0.6)
            ax.text(valor + 3, i, f"{valor}", va="center", fontsize=10.5, color=TINTA)
        else:
            ax.barh(i, -valor, left=restante + valor, color=color, height=0.6)
            ax.text(restante + 3, i, f"{valor}", va="center", fontsize=10.5, color=TINTA)
            restante += valor
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f[0] for f in filas], fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, len(limpias) * 1.12)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _titulo(ax, t["t_embudo"])
    fig.tight_layout()
    return fig


def test_ab(resultados: pd.DataFrame, idioma: str = "es"):
    t = TEXTOS[idioma]
    r = resultados.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 0.8 * len(r) + 1.8))
    ax.axvline(50, color=LINEA, ls="--", lw=1)
    ax.text(50.5, -0.55, t["empate"], ha="left", va="center", fontsize=9.5, color=SUAVE)
    for i, f in r.iterrows():
        claro = f["ic_bajo"] > 0.5
        color = VERDE if claro else ACENTO
        ax.plot([f["ic_bajo"] * 100, f["ic_alto"] * 100], [i, i], color=color, lw=3)
        ax.scatter(f["proporcion"] * 100, i, s=90, color=color, zorder=3)
        p = f"{f['proporcion']:.0%}"
        rango = f"{f['ic_bajo']:.0%} - {f['ic_alto']:.0%}"
        if idioma == "es":
            p, rango = p.replace("%", " %"), rango.replace("%", " %")
        ax.annotate(f"{p}  ({rango}, n={f['n']})", (f["ic_alto"] * 100, i), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=10, color=TINTA)
    ax.set_yticks(range(len(r)))
    ax.set_yticklabels([t["grupos"].get(g, g) for g in r["grupo"]], fontsize=11)
    ax.set_xlim(30, 112)
    ax.set_ylim(-0.8, len(r) - 0.5)
    ax.set_xticks(range(30, 101, 10))
    ax.set_xlabel(t["x_ab"])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _titulo(ax, t["t_ab"])
    fig.tight_layout()
    return fig
