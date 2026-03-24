"""
Template HTML para el correo INDIVIDUAL por agencia.
Cada sucursal recibe su propio correo con sus datos + ranking general.
"""

import base64
import io
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from config import LOGO_PATH


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _fmt_cop(valor: float) -> str:
    return f"${valor:,.0f}".replace(",", ".")

def _pct(hoy: float, ant: float) -> float:
    if ant == 0:
        return 100.0 if hoy > 0 else 0.0
    return ((hoy - ant) / ant) * 100

def _pct_color(p: float) -> str:
    if p >= 10:  return "#0D9E6A"
    if p >= 0:   return "#1A73C8"
    return "#D63B3B"

def _pct_icon(p: float) -> str:
    if p > 0:  return "&#9650;"
    if p < 0:  return "&#9660;"
    return "&#9644;"

def _logo_b64() -> Optional[str]:
    p = Path(LOGO_PATH)
    if p.exists():
        ext = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg","jpeg") else ext
        with open(p, "rb") as f:
            return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    return None

def _mensaje_motivacional(pct: float, nombre: str) -> str:
    if pct >= 20:
        return f"¡Increíble {nombre}! Superando el mes anterior por más del 20%. 🏆 ¡Sigan así!"
    if pct >= 5:
        return f"¡Muy bien {nombre}! Van por encima del mes anterior. 💪 ¡A cerrar el día con todo!"
    if pct >= 0:
        return f"¡Vamos {nombre}! Empatados con el mes anterior. 🎯 Un último esfuerzo marca la diferencia."
    if pct >= -10:
        return f"Atención {nombre}: ligeramente por debajo del mes anterior. 🔔 ¡Hay tiempo para recuperarse!"
    return f"¡Ánimo {nombre}! Estamos por debajo de la meta. 🚨 ¡Cada crédito cuenta hoy!"


# ─── MINI GRÁFICA DE DONA (monto hoy vs anterior) ────────────────────────────

def _generar_dona(monto_hoy: float, monto_ant: float) -> str:
    """Genera una gráfica de dona comparativa como base64 PNG."""
    fig, ax = plt.subplots(figsize=(4.2, 4.2), facecolor="#F0F4FA")
    ax.set_facecolor("#F0F4FA")

    maximo = max(monto_hoy, monto_ant, 1)
    # Dona exterior = mes anterior, dona interior = hoy
    tamaño   = [monto_ant, maximo - monto_ant]
    colores_a = ["#A8C8F0", "#E8EFF8"]

    tamaño_h  = [monto_hoy, maximo - monto_hoy]
    colores_h = ["#1A73C8", "#E8EFF8"]

    ax.pie(tamaño,   radius=1.0,  colors=colores_a,
           startangle=90, counterclock=False,
           wedgeprops=dict(width=0.28, edgecolor="#F0F4FA", linewidth=2))
    ax.pie(tamaño_h, radius=0.68, colors=colores_h,
           startangle=90, counterclock=False,
           wedgeprops=dict(width=0.28, edgecolor="#F0F4FA", linewidth=2))

    # Texto central
    pct = _pct(monto_hoy, monto_ant)
    color_pct = _pct_color(pct)
    signo = "+" if pct > 0 else ""
    ax.text(0,  0.12, f"{signo}{pct:.1f}%",
            ha="center", va="center", fontsize=16, fontweight="800",
            color=color_pct)
    ax.text(0, -0.18, "vs. mes ant.",
            ha="center", va="center", fontsize=8, color="#7A8CA0")

    leyenda = [
        mpatches.Patch(color="#1A73C8", label="Hoy"),
        mpatches.Patch(color="#A8C8F0", label="Mes anterior"),
    ]
    ax.legend(handles=leyenda, loc="lower center", fontsize=8,
              frameon=False, ncol=2, bbox_to_anchor=(0.5, -0.05))

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#F0F4FA")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ─── MINI BARRA DE RANKING ────────────────────────────────────────────────────

def _generar_ranking(
    sucursal_nom: str,
    datos_hoy: List[Dict],
) -> str:
    """Gráfica de barras horizontales con el ranking de todas las agencias."""
    sorted_d = sorted(datos_hoy, key=lambda x: x["monto"], reverse=True)
    nombres  = [d["sucursal_nom"] for d in sorted_d]
    montos   = [d["monto"] for d in sorted_d]
    colores  = [
        "#1A73C8" if n == sucursal_nom else "#C8D8EC"
        for n in nombres
    ]

    fig_h = max(5, len(nombres) * 0.38)
    fig, ax = plt.subplots(figsize=(7, fig_h), facecolor="#F0F4FA")
    ax.set_facecolor("#F0F4FA")

    y = np.arange(len(nombres))
    bars = ax.barh(y, montos, color=colores, height=0.62,
                   edgecolor="none", zorder=3)

    for i, (bar, m) in enumerate(zip(bars, montos)):
        ax.text(m * 1.01, bar.get_y() + bar.get_height() / 2,
                _fmt_cop(m), va="center", ha="left",
                fontsize=7.5,
                fontweight="800" if nombres[i] == sucursal_nom else "normal",
                color="#1A73C8" if nombres[i] == sucursal_nom else "#7A8CA0")

    ax.set_yticks(y)
    ax.set_yticklabels(nombres, fontsize=8.5)
    for i, label in enumerate(ax.get_yticklabels()):
        if nombres[i] == sucursal_nom:
            label.set_fontweight("bold")
            label.set_color("#0D2B5E")
        else:
            label.set_color("#6080A0")

    ax.invert_yaxis()
    ax.xaxis.set_visible(False)
    ax.spines[["top","right","bottom","left"]].set_visible(False)
    ax.yaxis.grid(False)
    ax.set_title("Ranking de Colocación — Todas las Agencias",
                 fontsize=10, fontweight="bold", color="#1E2D40", pad=10)

    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#F0F4FA")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ─── HTML PRINCIPAL ───────────────────────────────────────────────────────────

def construir_html_agencia(
    sucursal_id:   int,
    sucursal_nom:  str,
    monto_hoy:     float,
    monto_anterior: float,
    datos_hoy_todos: List[Dict],
    fecha: date,
) -> str:
    """
    Construye el HTML del correo individual para una agencia.

    El correo muestra:
      - Sus propios datos del día + comparativo mes anterior
      - Gráfica de dona propia
      - Ranking de todas las agencias (su barra resaltada)
    """
    pct       = _pct(monto_hoy, monto_anterior)
    pct_col   = _pct_color(pct)
    pct_icon  = _pct_icon(pct)
    signo     = "+" if pct > 0 else ""

    banner_bg     = "#E8F5E9" if pct >= 0 else "#FDECEA"
    banner_border = "#0D9E6A" if pct >= 0 else "#D63B3B"

    fecha_str  = fecha.strftime("%d de %B de %Y").title()
    dia_semana = fecha.strftime("%A").title()
    mensaje    = _mensaje_motivacional(pct, sucursal_nom)

    # Ranking posición
    sorted_d = sorted(datos_hoy_todos, key=lambda x: x["monto"], reverse=True)
    posicion = next((i+1 for i, d in enumerate(sorted_d)
                     if d["sucursal_nom"] == sucursal_nom), "-")
    total_agencias = len(sorted_d)
    total_red = sum(d["monto"] for d in datos_hoy_todos)
    pct_red = (monto_hoy / total_red * 100) if total_red > 0 else 0

    medalla = ""
    if posicion == 1: medalla = "🥇"
    elif posicion == 2: medalla = "🥈"
    elif posicion == 3: medalla = "🥉"

    # Gráficas
    dona_b64    = _generar_dona(monto_hoy, monto_anterior)
    ranking_b64 = _generar_ranking(sucursal_nom, datos_hoy_todos)

    # Logo
    logo_src = _logo_b64()
    logo_html = (
        f'<img src="{logo_src}" alt="Logo" '
        f'style="height:48px;max-width:180px;object-fit:contain;">'
        if logo_src else
        '<span style="font-size:20px;font-weight:800;color:#1A73C8;">&#9670; Cooperativa</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Colocación {sucursal_nom} - {fecha_str}</title>
</head>
<body style="margin:0;padding:0;background:#EDF1F7;
             font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#EDF1F7;padding:28px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
       style="max-width:600px;border-radius:16px;overflow:hidden;
              box-shadow:0 4px 24px rgba(0,0,0,0.10);">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#0D2B5E 0%,#1A73C8 60%,#34A8F5 100%);
               padding:24px 32px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td align="left" valign="middle">{logo_html}</td>
        <td align="right" valign="middle"
            style="color:#fff;font-size:11.5px;opacity:0.9;line-height:1.7;">
          <strong style="font-size:13px;display:block;">Reporte de Colocación</strong>
          {dia_semana}, {fecha_str}
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- SALUDO -->
  <tr>
    <td style="background:#FFFFFF;padding:26px 32px 14px;">
      <p style="margin:0 0 3px;font-size:11px;letter-spacing:2px;
                text-transform:uppercase;color:#1A73C8;font-weight:700;">
        Tu Reporte del Día
      </p>
      <h1 style="margin:0 0 6px;font-size:24px;font-weight:800;color:#0D2B5E;">
        {medalla} Agencia {sucursal_nom}
      </h1>
      <p style="margin:0;font-size:13px;color:#667;line-height:1.6;">
        Así va tu colocación de créditos hoy, comparada con el mismo
        período del <strong>mes anterior</strong>.
      </p>
    </td>
  </tr>

  <!-- BANNER MONTO + DONA -->
  <tr>
    <td style="background:#FFFFFF;padding:10px 32px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:{banner_bg};border-left:5px solid {banner_border};
                    border-radius:12px;overflow:hidden;">
        <tr>
          <!-- Texto izquierda -->
          <td style="padding:20px 20px 14px;vertical-align:middle;" width="58%">
            <p style="margin:0 0 3px;font-size:10.5px;color:#888;
                      text-transform:uppercase;letter-spacing:1.5px;">
              Colocado Hoy
            </p>
            <p style="margin:0 0 10px;font-size:28px;font-weight:800;color:#0D2B5E;">
              {_fmt_cop(monto_hoy)}
            </p>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:5px 12px;background:{pct_col};border-radius:20px;">
                  <span style="color:#fff;font-size:13px;font-weight:800;">
                    {pct_icon} {signo}{pct:.1f}% vs. mes ant.
                  </span>
                </td>
              </tr>
            </table>
            <p style="margin:10px 0 0;font-size:11.5px;color:#888;">
              Mes anterior: {_fmt_cop(monto_anterior)}
            </p>
          </td>
          <!-- Dona derecha -->
          <td style="padding:10px 16px 10px 0;text-align:center;
                     vertical-align:middle;" width="42%">
            <img src="data:image/png;base64,{dona_b64}"
                 alt="Comparativo" style="width:150px;display:inline-block;">
          </td>
        </tr>
        <!-- Fila mensaje -->
        <tr>
          <td colspan="2"
              style="padding:10px 20px 14px;
                     border-top:1px solid {banner_border}33;">
            <p style="margin:0;font-size:12.5px;font-weight:600;color:{banner_border};">
              {mensaje}
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- KPIs SECUNDARIOS -->
  <tr>
    <td style="background:#FFFFFF;padding:0 32px 22px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="border-spacing:8px;">
        <tr>
          <!-- Posición en red -->
          <td style="background:#F0F6FF;border-radius:10px;padding:14px 16px;
                     text-align:center;border:1px solid #D0E4F8;" width="33%">
            <p style="margin:0 0 3px;font-size:10px;color:#8899AA;
                      text-transform:uppercase;letter-spacing:1px;">Posición Red</p>
            <p style="margin:0;font-size:22px;font-weight:800;color:#0D2B5E;">
              {posicion}<span style="font-size:12px;color:#7A9ABB;">/{total_agencias}</span>
            </p>
          </td>
          <!-- Participación en red -->
          <td width="6px"></td>
          <td style="background:#F0F6FF;border-radius:10px;padding:14px 16px;
                     text-align:center;border:1px solid #D0E4F8;" width="33%">
            <p style="margin:0 0 3px;font-size:10px;color:#8899AA;
                      text-transform:uppercase;letter-spacing:1px;">Participación</p>
            <p style="margin:0;font-size:22px;font-weight:800;color:#1A73C8;">
              {pct_red:.1f}<span style="font-size:12px;color:#7A9ABB;">%</span>
            </p>
            <p style="margin:2px 0 0;font-size:9.5px;color:#AAB;">de la red</p>
          </td>
          <td width="6px"></td>
          <!-- Total red -->
          <td style="background:#F0F6FF;border-radius:10px;padding:14px 16px;
                     text-align:center;border:1px solid #D0E4F8;" width="33%">
            <p style="margin:0 0 3px;font-size:10px;color:#8899AA;
                      text-transform:uppercase;letter-spacing:1px;">Total Red Hoy</p>
            <p style="margin:0;font-size:14px;font-weight:800;color:#0D2B5E;">
              {_fmt_cop(total_red)}
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- RANKING GENERAL -->
  <tr>
    <td style="background:#FFFFFF;padding:0 32px 26px;">
      <p style="margin:0 0 10px;font-size:11px;color:#8899AA;
                text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">
        Tu posición en la red
      </p>
      <img src="data:image/png;base64,{ranking_b64}"
           alt="Ranking" style="width:100%;border-radius:10px;
           border:1px solid #E0E8F4;display:block;">
      <p style="margin:8px 0 0;font-size:10.5px;color:#AAB;text-align:center;">
        Tu agencia está resaltada en azul oscuro
      </p>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#0D2B5E;padding:18px 32px;text-align:center;">
      <p style="margin:0 0 3px;font-size:12px;color:#A0BBD8;font-weight:600;">
        Desarrollado por <span style="color:#34A8F5;">Gerencia TI</span>
      </p>
      <p style="margin:0;font-size:10.5px;color:#607A96;">
        Reporte automático diario · No responder este correo
      </p>
      <p style="margin:8px 0 0;font-size:10px;color:#405570;">
        &copy; {fecha.year} Gerencia de Tecnología e Información
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
