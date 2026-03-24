"""
Generador del HTML del correo electronico de colocacion diaria.
Diseno profesional con header, grafica, tabla de sucursales y footer.
"""

import base64
import os
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional

from config import LOGO_PATH

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _fmt_cop(valor: float) -> str:
    """Formatea un valor como moneda colombiana."""
    return f"${valor:,.0f}".replace(",", ".")


def _pct_color(pct: float) -> str:
    if pct >= 10:
        return "#0D9E6A"
    if pct >= 0:
        return "#1A73C8"
    return "#D63B3B"


def _pct_icon(pct: float) -> str:
    if pct > 0:
        return "&#9650;"   # ▲
    if pct < 0:
        return "&#9660;"   # ▼
    return "&#9644;"        # ▬


def _logo_b64() -> Optional[str]:
    """Carga el logo como base64 si existe."""
    p = Path(LOGO_PATH)
    if p.exists():
        ext = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        with open(p, "rb") as f:
            return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    return None


def _variacion(hoy: float, anterior: float) -> float:
    if anterior == 0:
        return 100.0 if hoy > 0 else 0.0
    return ((hoy - anterior) / anterior) * 100


# ─── TEMPLATE PRINCIPAL ───────────────────────────────────────────────────────

def construir_html(
    datos_hoy: List[Dict],
    datos_anterior: List[Dict],
    grafica_b64: str,
    fecha: date,
) -> str:
    """
    Construye el HTML completo del correo.
    """
    total_hoy = sum(d["monto"] for d in datos_hoy)
    mapa_ant  = {d["sucursal_nom"]: d["monto"] for d in datos_anterior}
    total_ant = sum(d["monto"] for d in datos_anterior)
    pct_total = _variacion(total_hoy, total_ant)

    fecha_str    = fecha.strftime("%d de %B de %Y").title()
    dia_semana   = fecha.strftime("%A").title()

    # --- LOGO ---
    logo_html = ""
    logo_src  = _logo_b64()
    if logo_src:
        logo_html = f'<img src="{logo_src}" alt="Logo" style="height:52px;max-width:200px;object-fit:contain;">'
    else:
        logo_html = '<span style="font-size:22px;font-weight:800;color:#1A73C8;letter-spacing:-0.5px;">&#9670; Cooperativa</span>'

    # --- FILA DE RESUMEN ---
    pct_icon  = _pct_icon(pct_total)
    pct_col   = _pct_color(pct_total)
    banner_bg = "#E8F5E9" if pct_total >= 0 else "#FDECEA"
    banner_border = "#0D9E6A" if pct_total >= 0 else "#D63B3B"

    banner_text = (
        "¡Excelente ritmo! Superando el mes anterior 🚀"
        if pct_total >= 0
        else "Atención: por debajo del mes anterior. ¡A impulsar los cierres! 💪"
    )

    # --- FILAS DE TABLA ---
    filas_tabla = ""
    sorted_datos = sorted(datos_hoy, key=lambda x: x["monto"], reverse=True)
    for i, d in enumerate(sorted_datos):
        nom   = d["sucursal_nom"]
        monto = d["monto"]
        ant   = mapa_ant.get(nom, 0)
        pct   = _variacion(monto, ant)
        col   = _pct_color(pct)
        icon  = _pct_icon(pct)
        bg    = "#FFFFFF" if i % 2 == 0 else "#F7F9FC"
        rank_medal = ""
        if i == 0: rank_medal = "&#129351;"   # 🥇
        elif i == 1: rank_medal = "&#129352;" # 🥈
        elif i == 2: rank_medal = "&#129353;" # 🥉

        filas_tabla += f"""
        <tr style="background:{bg};">
            <td style="padding:9px 14px;font-size:13px;color:#555;">{i+1}</td>
            <td style="padding:9px 14px;font-size:13.5px;font-weight:600;color:#1E2D40;">
                {rank_medal} {nom}
            </td>
            <td style="padding:9px 14px;font-size:13.5px;color:#1A73C8;font-weight:700;
                       text-align:right;">{_fmt_cop(monto)}</td>
            <td style="padding:9px 14px;font-size:12.5px;color:#777;text-align:right;">
                {_fmt_cop(ant)}
            </td>
            <td style="padding:9px 14px;font-size:13px;font-weight:700;color:{col};
                       text-align:center;">{icon} {abs(pct):.1f}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Colocacion Diaria - {fecha_str}</title>
</head>
<body style="margin:0;padding:0;background:#EDF1F7;font-family:'Segoe UI',Arial,sans-serif;">

<!-- WRAPPER -->
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#EDF1F7;padding:32px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0"
       style="max-width:640px;border-radius:16px;overflow:hidden;
              box-shadow:0 4px 24px rgba(0,0,0,0.10);">

  <!-- ═══════════ HEADER ═══════════ -->
  <tr>
    <td style="background:linear-gradient(135deg,#0D2B5E 0%,#1A73C8 60%,#34A8F5 100%);
               padding:28px 36px;text-align:center;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td align="left" valign="middle">{logo_html}</td>
        <td align="right" valign="middle"
            style="color:#FFFFFF;font-size:12px;opacity:0.85;line-height:1.6;">
          <strong style="font-size:14px;display:block;">Reporte de Colocacion</strong>
          {dia_semana}, {fecha_str}
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- ═══════════ TITULO ═══════════ -->
  <tr>
    <td style="background:#FFFFFF;padding:28px 36px 10px;">
      <p style="margin:0 0 4px;font-size:11px;letter-spacing:2px;
                text-transform:uppercase;color:#1A73C8;font-weight:700;">
        Creditos Desembolsados · {fecha_str}
      </p>
      <h1 style="margin:0 0 6px;font-size:26px;font-weight:800;color:#0D2B5E;
                 line-height:1.2;">
        Colocacion Diaria<br>
        <span style="color:#1A73C8;">de Creditos</span>
      </h1>
      <p style="margin:10px 0 0;font-size:13.5px;color:#555;line-height:1.6;">
        Aqui esta el resumen de creditos colocados hoy en todas las
        oficinas y centros de banca. Comparativo frente al mismo periodo
        del <strong>mes anterior</strong>.
      </p>
    </td>
  </tr>

  <!-- ═══════════ BANNER TOTAL ═══════════ -->
  <tr>
    <td style="background:#FFFFFF;padding:10px 36px 22px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:{banner_bg};border-left:5px solid {banner_border};
                    border-radius:10px;overflow:hidden;">
        <tr>
          <td style="padding:18px 22px;">
            <p style="margin:0 0 3px;font-size:11.5px;color:#666;
                      text-transform:uppercase;letter-spacing:1.5px;">
              Total Colocado Hoy
            </p>
            <p style="margin:0;font-size:30px;font-weight:800;color:#0D2B5E;">
              {_fmt_cop(total_hoy)}
            </p>
          </td>
          <td style="padding:18px 22px;text-align:right;">
            <p style="margin:0 0 2px;font-size:11px;color:#777;">vs. Mes Anterior</p>
            <p style="margin:0;font-size:22px;font-weight:800;color:{pct_col};">
              {pct_icon} {abs(pct_total):.1f}%
            </p>
            <p style="margin:4px 0 0;font-size:10.5px;color:#888;">
              Ant: {_fmt_cop(total_ant)}
            </p>
          </td>
        </tr>
        <tr>
          <td colspan="2"
              style="background:{banner_border}18;
                     padding:9px 22px;border-top:1px solid {banner_border}33;">
            <p style="margin:0;font-size:12.5px;color:{banner_border};font-weight:600;">
              {banner_text}
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ═══════════ GRAFICA ═══════════ -->
  <tr>
    <td style="background:#FFFFFF;padding:0 36px 24px;">
      <p style="margin:0 0 10px;font-size:11.5px;color:#888;
                text-transform:uppercase;letter-spacing:1.5px;">
        Comparativo por Sucursal
      </p>
      <img src="data:image/png;base64,{grafica_b64}"
           alt="Grafica Colocacion"
           style="width:100%;border-radius:10px;border:1px solid #E0E8F4;
                  display:block;">
    </td>
  </tr>

  <!-- ═══════════ TABLA DETALLE ═══════════ -->
  <tr>
    <td style="background:#FFFFFF;padding:0 36px 28px;">
      <p style="margin:0 0 10px;font-size:11.5px;color:#888;
                text-transform:uppercase;letter-spacing:1.5px;">
        Detalle por Oficina
      </p>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-radius:10px;overflow:hidden;
                    border:1px solid #E0E8F4;font-size:13px;">
        <thead>
          <tr style="background:linear-gradient(90deg,#0D2B5E,#1A73C8);color:#fff;">
            <th style="padding:10px 14px;text-align:left;font-weight:600;">#</th>
            <th style="padding:10px 14px;text-align:left;font-weight:600;">Sucursal / CB</th>
            <th style="padding:10px 14px;text-align:right;font-weight:600;">Hoy</th>
            <th style="padding:10px 14px;text-align:right;font-weight:600;">Mes Ant.</th>
            <th style="padding:10px 14px;text-align:center;font-weight:600;">Var.</th>
          </tr>
        </thead>
        <tbody>
          {filas_tabla}
          <tr style="background:#E8EFF8;">
            <td colspan="2"
                style="padding:11px 14px;font-weight:800;font-size:13.5px;color:#0D2B5E;">
              TOTAL GENERAL
            </td>
            <td style="padding:11px 14px;text-align:right;font-weight:800;
                       font-size:14px;color:#1A73C8;">
              {_fmt_cop(total_hoy)}
            </td>
            <td style="padding:11px 14px;text-align:right;font-size:12.5px;color:#666;">
              {_fmt_cop(total_ant)}
            </td>
            <td style="padding:11px 14px;text-align:center;font-weight:800;
                       font-size:13px;color:{pct_col};">
              {pct_icon} {abs(pct_total):.1f}%
            </td>
          </tr>
        </tbody>
      </table>
    </td>
  </tr>

  <!-- ═══════════ MENSAJE MOTIVACIONAL ═══════════ -->
  <tr>
    <td style="background:#F0F6FF;padding:20px 36px;
               border-top:3px solid #1A73C8;border-bottom:3px solid #1A73C8;">
      <p style="margin:0;font-size:14px;color:#1A4080;font-style:italic;
                line-height:1.7;text-align:center;">
        "Cada credito colocado representa una oportunidad real para
        nuestros asociados. <strong>Juntos construimos progreso.</strong>"
      </p>
    </td>
  </tr>

  <!-- ═══════════ FOOTER ═══════════ -->
  <tr>
    <td style="background:#0D2B5E;padding:20px 36px;text-align:center;">
      <p style="margin:0 0 4px;font-size:12.5px;color:#A0BBD8;font-weight:600;">
        Desarrollado por <span style="color:#34A8F5;">Gerencia TI</span>
      </p>
      <p style="margin:0;font-size:11px;color:#607A96;">
        Este reporte se genera automaticamente cada dia a las 8:00 a.m.<br>
        No responder a este correo &mdash; es un envio automatizado.
      </p>
      <p style="margin:10px 0 0;font-size:10.5px;color:#405570;">
        &copy; {fecha.year} Gerencia de Tecnologia e Informacion
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>"""

    return html
