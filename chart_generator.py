"""
Generacion de grafica de barras comparativa (hoy vs. mes anterior).
Retorna la imagen como base64 para incrustar en el HTML del correo.
"""

import io
import base64
import logging
from typing import List, Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

logger = logging.getLogger(__name__)

COLOR_HOY   = "#1A73C8"
COLOR_ANT   = "#A8C8F0"
COLOR_BG    = "#F0F4FA"
COLOR_GRID  = "#DDE4EF"
COLOR_TEXT  = "#1E2D40"


def _fmt(x, _):
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:.0f}"


def generar_grafica(datos_hoy: List[Dict], datos_anterior: List[Dict], top_n: int = 12) -> str:
    """
    Genera grafica de barras agrupadas y retorna base64 PNG.
    """
    monto_ant = {d["sucursal_nom"]: d["monto"] for d in datos_anterior}
    sorted_hoy = sorted(datos_hoy, key=lambda x: x["monto"], reverse=True)[:top_n]

    nombres  = [d["sucursal_nom"] for d in sorted_hoy]
    montos_h = [d["monto"] for d in sorted_hoy]
    montos_a = [monto_ant.get(n, 0) for n in nombres]

    fig_w = max(14, len(nombres) * 1.15)
    fig, ax = plt.subplots(figsize=(fig_w, 6), facecolor=COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    x     = np.arange(len(nombres))
    ancho = 0.38

    bars_h = ax.bar(x - ancho / 2, montos_h, ancho, label="Hoy",
                    color=COLOR_HOY, zorder=3, linewidth=0, edgecolor="none")
    bars_a = ax.bar(x + ancho / 2, montos_a, ancho, label="Mes anterior",
                    color=COLOR_ANT, zorder=3, linewidth=0, edgecolor="none")

    for bar in bars_h:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.015,
                    _fmt(h, None), ha="center", va="bottom",
                    fontsize=7.5, color=COLOR_HOY, fontweight="bold")

    for bar in bars_a:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.015,
                    _fmt(h, None), ha="center", va="bottom",
                    fontsize=7, color="#6090B8")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt))
    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=30, ha="right", fontsize=8.5, color=COLOR_TEXT)
    ax.yaxis.label.set_color(COLOR_TEXT)
    ax.tick_params(colors=COLOR_TEXT, labelsize=8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_GRID)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    legend = ax.legend(frameon=True, framealpha=0.9, fontsize=9,
                       facecolor="white", edgecolor=COLOR_GRID,
                       loc="upper right")
    for text in legend.get_texts():
        text.set_color(COLOR_TEXT)

    ax.set_title("Colocacion Diaria de Creditos por Sucursal",
                 fontsize=13, fontweight="bold", color=COLOR_TEXT, pad=14)

    plt.tight_layout(pad=1.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                facecolor=COLOR_BG)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
