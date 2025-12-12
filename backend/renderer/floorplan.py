from typing import Dict, Any, List, Tuple
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

MM_TO_PT = 72.0 / 25.4  # 1mm in points

def m_to_mm(m: float) -> float:
    return m * 1000.0

def escape(s: str) -> str:
    return (s.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
              .replace("'", "&apos;"))

def validate_plan(plan: Dict[str, Any]) -> None:
    for k in ["plot", "setbacks", "rooms"]:
        if k not in plan:
            raise ValueError(f"Missing '{k}' in plan")

    plot = plan["plot"]
    if plot["w"] <= 0 or plot["h"] <= 0:
        raise ValueError("Plot dimensions must be > 0")

    sb = plan["setbacks"]
    for s in ["left", "right", "front", "back"]:
        if sb.get(s, None) is None or sb[s] < 0:
            raise ValueError(f"Invalid setback '{s}'")

    build_w = plot["w"] - sb["left"] - sb["right"]
    build_h = plot["h"] - sb["front"] - sb["back"]
    if build_w <= 0 or build_h <= 0:
        raise ValueError("Setbacks leave no buildable area")

    bx0, by0 = sb["left"], sb["front"]
    bx1, by1 = bx0 + build_w, by0 + build_h

    for r in plan["rooms"]:
        for f in ["name", "x", "y", "w", "h"]:
            if f not in r:
                raise ValueError(f"Room missing '{f}'")
        if r["w"] <= 0 or r["h"] <= 0:
            raise ValueError(f"Room '{r['name']}' has invalid size")
        rx0, ry0 = r["x"], r["y"]
        rx1, ry1 = rx0 + r["w"], ry0 + r["h"]
        if not (bx0 <= rx0 and by0 <= ry0 and rx1 <= bx1 and ry1 <= by1):
            raise ValueError(f"Room '{r['name']}' is outside buildable area")

def plan_to_svg(plan: Dict[str, Any], px_per_m: int = 70, margin_px: int = 20) -> str:
    validate_plan(plan)

    plot_w = plan["plot"]["w"]
    plot_h = plan["plot"]["h"]
    sb = plan["setbacks"]
    title = plan.get("meta", {}).get("title", "Floor Plan")

    W = int(plot_w * px_per_m) + margin_px * 2
    H = int(plot_h * px_per_m) + margin_px * 2

    def X(m: float) -> float:
        return margin_px + m * px_per_m

    def Y(m: float) -> float:
        return margin_px + (plot_h - m) * px_per_m

    def rect(x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        return (X(x), Y(y + h), w * px_per_m, h * px_per_m)

    plot_x, plot_y, plot_rw, plot_rh = rect(0, 0, plot_w, plot_h)
    build_x, build_y, build_rw, build_rh = rect(
        sb["left"], sb["front"],
        plot_w - sb["left"] - sb["right"],
        plot_h - sb["front"] - sb["back"]
    )

    parts: List[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    parts.append(f'<text x="{margin_px}" y="{margin_px - 4}" font-size="14" font-family="Inter, Arial">{escape(title)}</text>')
    parts.append(f'<rect x="{plot_x}" y="{plot_y}" width="{plot_rw}" height="{plot_rh}" fill="none" stroke="black" stroke-width="2"/>')
    parts.append(f'<rect x="{build_x}" y="{build_y}" width="{build_rw}" height="{build_rh}" fill="none" stroke="black" stroke-dasharray="6 4" stroke-width="1"/>')

    for r in plan["rooms"]:
        rx, ry, rw, rh = rect(r["x"], r["y"], r["w"], r["h"])
        parts.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="none" stroke="black" stroke-width="1.5"/>')
        cx = rx + rw / 2
        cy = ry + rh / 2
        parts.append(f'<text x="{cx}" y="{cy}" font-size="12" font-family="Inter, Arial" text-anchor="middle" dominant-baseline="middle">{escape(str(r["name"]))}</text>')

    parts.append(f'<text x="{margin_px}" y="{H - 8}" font-size="11" font-family="Inter, Arial">Preview scale: {px_per_m}px ≈ 1m</text>')
    parts.append('</svg>')
    return "\n".join(parts)

def plan_to_pdf_bytes(plan: Dict[str, Any]) -> bytes:
    validate_plan(plan)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    page_w, page_h = A4

    title = plan.get("meta", {}).get("title", "Floor Plan")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(24, page_h - 28, title)

    margin = 36
    plot_w_m = plan["plot"]["w"]
    plot_h_m = plan["plot"]["h"]
    plot_w_pt = m_to_mm(plot_w_m) * MM_TO_PT
    plot_h_pt = m_to_mm(plot_h_m) * MM_TO_PT

    max_w = page_w - 2 * margin
    max_h = page_h - 2 * margin - 24
    scale = min(max_w / plot_w_pt, max_h / plot_h_pt)

    ox = margin
    oy = margin

    def P(x_m: float, y_m: float) -> Tuple[float, float]:
        x_pt = (m_to_mm(x_m) * MM_TO_PT) * scale + ox
        y_pt = (m_to_mm(y_m) * MM_TO_PT) * scale + oy
        return x_pt, y_pt

    x0, y0 = P(0, 0)
    x1, y1 = P(plot_w_m, plot_h_m)
    c.setLineWidth(2)
    c.rect(x0, y0, x1 - x0, y1 - y0)

    sb = plan["setbacks"]
    bx0, by0 = P(sb["left"], sb["front"])
    bx1, by1 = P(plot_w_m - sb["right"], plot_h_m - sb["back"])
    c.setLineWidth(1)
    c.setDash(6, 4)
    c.rect(bx0, by0, bx1 - bx0, by1 - by0)
    c.setDash()

    c.setFont("Helvetica", 10)
    c.setLineWidth(1.5)
    for r in plan["rooms"]:
        rx0, ry0 = P(r["x"], r["y"])
        rx1, ry1 = P(r["x"] + r["w"], r["y"] + r["h"])
        c.rect(rx0, ry0, rx1 - rx0, ry1 - ry0)
        cx = (rx0 + rx1) / 2
        cy = (ry0 + ry1) / 2
        c.drawCentredString(cx, cy, str(r["name"]))

    c.setFont("Helvetica", 9)
    c.drawString(margin, 18, "Generated by SQ.AI (renderer v1)")
    c.showPage()
    c.save()

    return buf.getvalue()
