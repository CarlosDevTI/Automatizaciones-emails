import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from reports.data_processor import BranchPerformance


def _money_axis(value, _position):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def _figure_to_png_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor(), pad_inches=0.15)
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def generate_branch_comparison_chart(branch: BranchPerformance) -> bytes:
    labels = ["Monto actual", "Meta mensual"]
    values = [float(branch.current_amount), float(branch.monthly_target)]
    colors = ["#2563a6", "#d9e3ef"]

    fig, ax = plt.subplots(figsize=(4.6, 3.0), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    bars = ax.bar(labels, values, color=colors, width=0.55)
    ax.yaxis.set_major_formatter(FuncFormatter(_money_axis))
    ax.grid(axis="y", color="#dce5ee", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#dce5ee")
    ax.tick_params(axis="x", labelsize=9, colors="#17324d")
    ax.tick_params(axis="y", labelsize=8, colors="#5c7389")
    ax.set_title("Avance frente a la meta", fontsize=11, fontweight="bold", color="#17324d", pad=10)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + (bar.get_width() / 2),
            height + max(values + [1]) * 0.02,
            _money_axis(height, None),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#17324d",
            fontweight="bold",
        )

    fig.tight_layout()
    return _figure_to_png_bytes(fig)


def generate_management_bar_chart(branches: list[BranchPerformance]) -> bytes:
    if not branches:
        fig, ax = plt.subplots(figsize=(5.4, 2.4), facecolor="#ffffff")
        ax.text(0.5, 0.5, "Sin datos para graficar", ha="center", va="center", color="#17324d")
        ax.axis("off")
        return _figure_to_png_bytes(fig)

    ordered = list(reversed(branches))
    labels = [branch.branch_name for branch in ordered]
    current_values = [float(branch.current_amount) for branch in ordered]
    target_values = [float(branch.monthly_target) for branch in ordered]
    chart_height = min(max(4.6, len(labels) * 0.28), 7.2)

    fig, ax = plt.subplots(figsize=(5.4, chart_height), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    y_positions = np.arange(len(labels))
    bar_height = 0.34

    ax.barh(y_positions - (bar_height / 2), current_values, bar_height, color="#2563a6", label="Monto actual")
    ax.barh(y_positions + (bar_height / 2), target_values, bar_height, color="#d9e3ef", label="Meta mensual")

    ax.xaxis.set_major_formatter(FuncFormatter(_money_axis))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8, color="#17324d")
    ax.tick_params(axis="x", labelsize=8, colors="#5c7389")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.grid(axis="x", color="#dce5ee", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Cumplimiento de meta por sucursal", fontsize=11, fontweight="bold", color="#17324d", pad=10)
    fig.tight_layout()
    return _figure_to_png_bytes(fig)
