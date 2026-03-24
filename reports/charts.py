import base64
import io
from decimal import Decimal

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


def _figure_to_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def generate_branch_donut_chart(branch: BranchPerformance, total_amount: Decimal) -> str:
    other_amount = max(float(total_amount - branch.amount), 0.0)
    values = [float(branch.amount), other_amount]
    colors = ["#1f6aa5", "#d9e7f2"]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), facecolor="#f6f8fb")
    ax.pie(
        values,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.42, "edgecolor": "white"},
    )
    ax.text(0, 0.08, branch.branch_name, ha="center", va="center", fontsize=10, fontweight="bold", color="#16324f")
    ax.text(0, -0.12, f"{branch.participation_pct:.2f}%", ha="center", va="center", fontsize=12, color="#1f6aa5")
    ax.set(aspect="equal")
    return _figure_to_base64(fig)


def generate_management_bar_chart(branches: list[BranchPerformance]) -> str:
    if not branches:
        fig, ax = plt.subplots(figsize=(8, 3), facecolor="#f6f8fb")
        ax.text(0.5, 0.5, "Sin datos para graficar", ha="center", va="center")
        ax.axis("off")
        return _figure_to_base64(fig)

    labels = [branch.branch_name for branch in branches]
    today_values = [float(branch.amount) for branch in branches]
    previous_values = [float(branch.previous_amount) for branch in branches]
    width = max(10, len(labels) * 0.55)

    fig, ax = plt.subplots(figsize=(width, 5.4), facecolor="#f6f8fb")
    ax.set_facecolor("#f6f8fb")

    x_positions = np.arange(len(labels))
    bar_width = 0.38

    ax.bar(x_positions - (bar_width / 2), today_values, bar_width, color="#1f6aa5", label="Hoy", zorder=3)
    ax.bar(x_positions + (bar_width / 2), previous_values, bar_width, color="#86b9dd", label="Mes anterior", zorder=3)

    ax.yaxis.set_major_formatter(FuncFormatter(_money_axis))
    ax.grid(axis="y", color="#dbe6ef", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#dbe6ef")
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(frameon=False)
    ax.set_title("Colocacion diaria vs. mes anterior", fontsize=13, fontweight="bold", color="#16324f")
    fig.tight_layout()
    return _figure_to_base64(fig)
