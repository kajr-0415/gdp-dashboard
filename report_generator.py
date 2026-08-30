"""
PAN-MED — Branded PDF Report Generator
========================================
Builds a polished, print-ready diagnostic report PDF that matches the
site's dark-purple visual identity, instead of the old bare-bones fpdf
text dump. Pure reportlab — no extra system dependencies.

Usage:
    from report_generator import generate_pdf_report
    pdf_bytes = generate_pdf_report(
        patient_image=pil_img,           # PIL.Image, the uploaded/captured photo
        gradcam_original=pil_orig,       # PIL.Image (224x224 resized original)
        gradcam_heatmap=pil_heat,        # PIL.Image (JET heatmap)
        gradcam_overlay=pil_overlay,     # PIL.Image (blended overlay)
        diagnosis_name="Melanoma",
        diagnosis_code="mel",
        confidence=87.3,                 # 0-100 float
        risk_label="HIGH RISK",
        risk_tier="red",                 # red | orange | yellow | green
        top5=[("Melanoma", 87.3), ("Melanocytic Nevi", 6.1), ...],
        implication={"category": "...", "description": "...", "actions": [...]},
        report_id="PM-20260824-1F3A",
        generated_at="August 24, 2026, 3:41 PM",
    )
"""

import io
import re
from datetime import datetime

# Strip emoji / pictographs before rendering — reportlab's built-in Helvetica
# font has no emoji glyphs and would otherwise show tofu boxes.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\uFE0F"
    "]+", flags=re.UNICODE)


def _clean(text):
    if not isinstance(text, str):
        return text
    return _EMOJI_RE.sub("", text).strip()

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, Flowable, Image as RLImage, KeepTogether, HRFlowable,
)
from reportlab.pdfgen import canvas as pdfcanvas
from PIL import Image as PILImage


# ── Brand palette ────────────────────────────────────────────────────────────
INK        = colors.HexColor("#0f0028")
PANEL      = colors.HexColor("#150a35")
PANEL_2    = colors.HexColor("#1c0f42")
PURPLE_HI  = colors.HexColor("#9900ff")
PURPLE_LO  = colors.HexColor("#4400bb")
LILAC      = colors.HexColor("#c77dff")
LILAC_DIM  = colors.HexColor("#8a6bb0")
WHITE      = colors.HexColor("#ffffff")
TRACK_BG   = colors.HexColor("#2a1660")

TIER_COLORS = {
    "red":    (colors.HexColor("#ff4d4d"), colors.HexColor("#3a0f14")),
    "orange": (colors.HexColor("#ffb347"), colors.HexColor("#3a2508")),
    "yellow": (colors.HexColor("#ffd166"), colors.HexColor("#3a3008")),
    "green":  (colors.HexColor("#06d6a0"), colors.HexColor("#08322a")),
}

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm


# ── Style sheet ───────────────────────────────────────────────────────────────
_ss = getSampleStyleSheet()

STYLES = {
    "h1": ParagraphStyle("h1", parent=_ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=20, leading=24, textColor=WHITE, spaceAfter=2),
    "h2": ParagraphStyle("h2", parent=_ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=12.5, leading=16, textColor=WHITE, spaceAfter=8),
    "eyebrow": ParagraphStyle("eyebrow", parent=_ss["Normal"], fontName="Helvetica-Bold",
                               fontSize=8, leading=10, textColor=LILAC, spaceAfter=4,
                               tracking=1),
    "body": ParagraphStyle("body", parent=_ss["Normal"], fontName="Helvetica",
                            fontSize=9.3, leading=14.5, textColor=colors.HexColor("#d7bfff")),
    "body_dim": ParagraphStyle("body_dim", parent=_ss["Normal"], fontName="Helvetica",
                                fontSize=8.3, leading=12, textColor=LILAC_DIM),
    "meta": ParagraphStyle("meta", parent=_ss["Normal"], fontName="Helvetica",
                            fontSize=8, leading=11, textColor=LILAC_DIM),
    "meta_right": ParagraphStyle("meta_right", parent=_ss["Normal"], fontName="Helvetica",
                                  fontSize=8, leading=11, textColor=LILAC_DIM, alignment=TA_LEFT),
    "diag_name": ParagraphStyle("diag_name", parent=_ss["Normal"], fontName="Helvetica-Bold",
                                 fontSize=17, leading=20, textColor=WHITE),
    "diag_code": ParagraphStyle("diag_code", parent=_ss["Normal"], fontName="Courier",
                                 fontSize=8.5, leading=11, textColor=LILAC_DIM),
    "action": ParagraphStyle("action", parent=_ss["Normal"], fontName="Helvetica",
                              fontSize=8.6, leading=12, textColor=colors.HexColor("#e6d9ff")),
    "disclaimer": ParagraphStyle("disclaimer", parent=_ss["Normal"], fontName="Helvetica-Oblique",
                                  fontSize=7.6, leading=11.2, textColor=colors.HexColor("#ffcf8f")),
    "img_caption": ParagraphStyle("img_caption", parent=_ss["Normal"], fontName="Helvetica",
                                   fontSize=7.6, leading=10, textColor=LILAC_DIM,
                                   alignment=TA_CENTER),
}


# ── Custom flowables ────────────────────────────────────────────────────────
class RoundedPanel(Flowable):
    """A filled rounded-rect background sized to its content; used purely as a
    background layer under a Table via KeepInFrame is finicky in reportlab,
    so instead we draw panels directly as backgrounds on Table cells."""
    pass


class ProgressBar(Flowable):
    """A horizontal rounded progress/confidence bar."""
    def __init__(self, width, height, pct, fg=PURPLE_HI, bg=TRACK_BG):
        super().__init__()
        self.width = width
        self.height = height
        self.pct = max(0, min(100, pct))
        self.fg = fg
        self.bg = bg

    def draw(self):
        c = self.canv
        r = self.height / 2
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.width, self.height, r, fill=1, stroke=0)
        fw = max(self.height, self.width * self.pct / 100.0)
        c.setFillColor(self.fg)
        c.roundRect(0, 0, fw, self.height, r, fill=1, stroke=0)

    def wrap(self, availWidth, availHeight):
        return self.width, self.height


class RiskBadge(Flowable):
    """A pill-shaped risk badge, e.g. 'HIGH RISK'."""
    def __init__(self, text, tier="yellow", font_size=8.5, pad_x=10, height=18):
        super().__init__()
        self.text = text
        self.fg, self.bg = TIER_COLORS.get(tier, TIER_COLORS["yellow"])
        self.font_size = font_size
        self.pad_x = pad_x
        self.height = height
        c = pdfcanvas.Canvas(io.BytesIO())
        c.setFont("Helvetica-Bold", font_size)
        self.text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
        self.width = self.text_width + pad_x * 2

    def draw(self):
        c = self.canv
        r = self.height / 2
        c.setFillColor(self.bg)
        c.setStrokeColor(self.fg)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, self.width, self.height, r, fill=1, stroke=1)
        c.setFillColor(self.fg)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawCentredString(self.width / 2, self.height / 2 - self.font_size * 0.36, self.text)

    def wrap(self, availWidth, availHeight):
        return self.width, self.height


class ConfidenceRing(Flowable):
    """A circular confidence gauge (arc), drawn with simple polygon segments."""
    def __init__(self, diameter, pct, fg=PURPLE_HI, bg=TRACK_BG, label_size=15):
        super().__init__()
        self.d = diameter
        self.pct = max(0, min(100, pct))
        self.fg = fg
        self.bg = bg
        self.label_size = label_size

    def wrap(self, availWidth, availHeight):
        return self.d, self.d

    def draw(self):
        c = self.canv
        cx = cy = self.d / 2
        radius_out = self.d / 2 - 2
        thickness = self.d * 0.13

        c.saveState()
        c.setLineWidth(thickness)
        c.setLineCap(1)  # round caps

        # background ring
        c.setStrokeColor(self.bg)
        c.circle(cx, cy, radius_out - thickness / 2, stroke=1, fill=0)

        # foreground arc (starts at 90deg / top, clockwise)
        c.setStrokeColor(self.fg)
        extent = -360.0 * (self.pct / 100.0)
        c.arc(cx - (radius_out - thickness / 2), cy - (radius_out - thickness / 2),
              cx + (radius_out - thickness / 2), cy + (radius_out - thickness / 2),
              startAng=90, extent=extent)
        c.restoreState()

        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", self.label_size)
        c.drawCentredString(cx, cy - self.label_size * 0.35, f"{self.pct:.0f}%")
        c.setFillColor(LILAC_DIM)
        c.setFont("Helvetica", 6.4)
        c.drawCentredString(cx, cy - self.label_size * 0.35 - 9, "CONFIDENCE")


class _Square(Flowable):
    """A small colored square used as a section-title accent (in place of emoji,
    which reportlab's built-in fonts can't render)."""
    def __init__(self, size=9, color=PURPLE_HI):
        super().__init__()
        self.size = size
        self.color = color

    def wrap(self, availWidth, availHeight):
        return self.size, self.size

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 1, self.size, self.size, 2, fill=1, stroke=0)


def _section_title(text, accent=PURPLE_HI):
    """Small colored square + bold heading, laid out in a single row."""
    sq = _Square(9, accent)
    t = Table([[sq, Paragraph(text, STYLES["h2"])]], colWidths=[16, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _panel_table(content_flowables, bg=PANEL, border=colors.HexColor("#3d1f7a"),
                  pad=12, width=None):
    """Wrap a list of flowables in a single-cell Table styled as a rounded card
    (reportlab doesn't do true rounded corners on tables, so we simulate a
    clean bordered panel which reads the same in a PDF viewer)."""
    t = Table([[content_flowables]], colWidths=[width] if width else None)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.75, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _pil_to_rlimage(pil_img: PILImage.Image, width):
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    ratio = pil_img.height / pil_img.width
    return RLImage(buf, width=width, height=width * ratio)


def _header_footer(canvas_obj, doc, report_id, generated_at):
    canvas_obj.saveState()
    # top brand band
    canvas_obj.setFillColor(INK)
    canvas_obj.rect(0, PAGE_H - 26 * mm, PAGE_W, 26 * mm, fill=1, stroke=0)
    # gradient-ish accent strip
    canvas_obj.setFillColor(PURPLE_HI)
    canvas_obj.rect(0, PAGE_H - 26 * mm, PAGE_W, 1.4, fill=1, stroke=0)

    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 15)
    canvas_obj.drawString(MARGIN, PAGE_H - 15 * mm, "✕ PAN")
    w = canvas_obj.stringWidth("✕ PAN", "Helvetica-Bold", 15)
    canvas_obj.setFillColor(LILAC)
    canvas_obj.drawString(MARGIN + w, PAGE_H - 15 * mm, "MED")

    canvas_obj.setFillColor(LILAC_DIM)
    canvas_obj.setFont("Helvetica", 7.6)
    canvas_obj.drawString(MARGIN, PAGE_H - 20 * mm, "AI-Assisted Dermatological Screening Report")

    canvas_obj.setFont("Helvetica", 7.6)
    canvas_obj.drawRightString(PAGE_W - MARGIN, PAGE_H - 15 * mm, f"Report ID: {report_id}")
    canvas_obj.drawRightString(PAGE_W - MARGIN, PAGE_H - 20 * mm, generated_at)

    # footer
    canvas_obj.setFillColor(LILAC_DIM)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(MARGIN, 10 * mm,
                           "Generated by PAN-MED AI — an assistive screening tool, not a medical diagnosis.")
    canvas_obj.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
    canvas_obj.setStrokeColor(colors.HexColor("#3d1f7a"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    canvas_obj.restoreState()


def generate_pdf_report(
    diagnosis_name,
    diagnosis_code,
    confidence,
    risk_label,
    risk_tier,
    top5,
    implication,
    gradcam_original=None,
    gradcam_heatmap=None,
    gradcam_overlay=None,
    report_id=None,
    generated_at=None,
):
    """Returns PDF bytes for a fully-styled PAN-MED diagnostic report."""
    if report_id is None:
        report_id = "PM-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    if generated_at is None:
        generated_at = datetime.now().strftime("%B %d, %Y, %I:%M %p")

    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=32 * mm, bottomMargin=18 * mm,
        title=f"PAN-MED Report — {diagnosis_name}",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                   doc.width, doc.height, id="main")

    def on_page(c, d):
        _header_footer(c, d, report_id, generated_at)

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])

    story = []
    content_w = doc.width

    # ── Diagnosis summary card ────────────────────────────────────────────
    badge = RiskBadge(risk_label, tier=risk_tier)
    ring = ConfidenceRing(58, confidence)

    diag_block = [
        Paragraph("PRIMARY FINDING", STYLES["eyebrow"]),
        Paragraph(_clean(diagnosis_name), STYLES["diag_name"]),
        Spacer(1, 2),
        Paragraph(f"Code: {diagnosis_code.upper()}", STYLES["diag_code"]),
        Spacer(1, 10),
        badge,
    ]
    diag_left = Table([[f] for f in diag_block])
    diag_left.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    summary_row = Table([[diag_left, ring]],
                         colWidths=[content_w - 24 - 70, 70])
    summary_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))

    story.append(_panel_table(summary_row, width=content_w))
    story.append(Spacer(1, 10))

    # ── Grad-CAM visualization ────────────────────────────────────────────
    if gradcam_original and gradcam_heatmap and gradcam_overlay:
        img_w = (content_w - 24 - 2 * 10) / 3
        imgs = [
            [_pil_to_rlimage(gradcam_original, img_w), _pil_to_rlimage(gradcam_heatmap, img_w),
             _pil_to_rlimage(gradcam_overlay, img_w)],
            [Paragraph("Original", STYLES["img_caption"]),
             Paragraph("Grad-CAM Heatmap", STYLES["img_caption"]),
             Paragraph("Overlay", STYLES["img_caption"])],
        ]
        img_table = Table(imgs, colWidths=[img_w, img_w, img_w], hAlign="LEFT")
        img_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 1), (-1, 1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        gcam_block = [
            _section_title("GRADCAM VISUALIZATION", PURPLE_HI),
            Paragraph("Regions of the image that most influenced the AI's decision.", STYLES["body_dim"]),
            Spacer(1, 8),
            img_table,
        ]
        gcam_stack = Table([[f] for f in gcam_block])
        gcam_stack.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(_panel_table(gcam_stack, width=content_w))
        story.append(Spacer(1, 10))

    # ── Top 5 predictions ─────────────────────────────────────────────────
    rows = [[Paragraph("TOP 5 PREDICTIONS", STYLES["eyebrow"]), "", ""]]
    pct_col_w = 38
    label_col_w = 140
    bar_w = content_w - 24 - label_col_w - pct_col_w
    for cname, pct in top5:
        rows.append([
            Paragraph(_clean(cname), STYLES["body"]),
            ProgressBar(bar_w, 7, pct),
            Paragraph(f"{pct:.1f}%", STYLES["body_dim"]),
        ])
    top5_table = Table(rows, colWidths=[label_col_w, bar_w, pct_col_w])
    top5_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(_panel_table(top5_table, width=content_w))
    story.append(Spacer(1, 10))

    # ── Clinical implications ─────────────────────────────────────────────
    fg, _ = TIER_COLORS.get(risk_tier, TIER_COLORS["yellow"])
    action_chips = []
    for a in implication.get("actions", []):
        action_chips.append(Paragraph(f"&#10003;  {_clean(a)}", STYLES["action"]))
    # lay chips out 2 per row
    chip_rows = [action_chips[i:i + 2] for i in range(0, len(action_chips), 2)]
    for r in chip_rows:
        while len(r) < 2:
            r.append("")
    chip_table = Table(chip_rows, colWidths=[(content_w - 24) / 2] * 2) if chip_rows else None
    if chip_table:
        chip_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

    impl_inner = [
        _section_title("CLINICAL IMPLICATIONS", fg),
        Spacer(1, 4),
        Paragraph(_clean(implication.get("category", "")), ParagraphStyle(
            "cat", parent=STYLES["body"], textColor=fg, fontName="Helvetica-Bold", fontSize=9.5)),
        Spacer(1, 6),
        Paragraph(_clean(implication.get("description", "")), STYLES["body"]),
        Spacer(1, 10),
        Paragraph("RECOMMENDED ACTIONS", STYLES["eyebrow"]),
        Spacer(1, 3),
    ]
    if chip_table:
        impl_inner.append(chip_table)

    impl_stack = Table([[f] for f in impl_inner])
    impl_stack.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(_panel_table(impl_stack, bg=PANEL_2, border=fg, width=content_w))
    story.append(Spacer(1, 10))

    # ── Disclaimer ─────────────────────────────────────────────────────────
    disc = Paragraph(
        "MEDICAL DISCLAIMER: PAN-MED is an AI-assisted screening tool intended to support, "
        "not replace, professional medical judgment. This report does not constitute a diagnosis. "
        "Please consult a licensed dermatologist for accurate evaluation and treatment.",
        STYLES["disclaimer"])
    disc_panel = _panel_table(disc, bg=colors.HexColor("#2b1a06"),
                               border=colors.HexColor("#8a5a1a"), width=content_w)
    story.append(disc_panel)

    doc.build(story)
    return buf.getvalue()
