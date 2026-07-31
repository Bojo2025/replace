"""
Generate a professional A4 replacement-sheet PDF using ReportLab.
"""

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.platypus import PageBreak
from reportlab.pdfgen import canvas as rl_canvas

import replacement_logic as logic
from ui.screen2_assign import _split_class_room

# ── Colour palette (matches the UI) ──────────────────────────────────────────
HEADER_BG   = colors.HexColor("#1A237E")
PRIMARY     = colors.HexColor("#1565C0")
ACCENT      = colors.HexColor("#1E88E5")
LIGHT_BLUE  = colors.HexColor("#E3F2FD")
SUCCESS     = colors.HexColor("#2E7D32")
SUCCESS_LT  = colors.HexColor("#E8F5E9")
DANGER      = colors.HexColor("#C62828")
DANGER_LT   = colors.HexColor("#FFEBEE")
WARNING     = colors.HexColor("#E65100")
WARNING_LT  = colors.HexColor("#FFF3E0")
BORDER      = colors.HexColor("#CBD5E1")
TEXT        = colors.HexColor("#1E293B")
TEXT_MUTED  = colors.HexColor("#64748B")
ROW_ALT     = colors.HexColor("#F8FAFC")
WHITE       = colors.white
BLACK       = colors.black

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 2 * cm
T_MARGIN = 2.5 * cm
B_MARGIN = 2 * cm


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    return {
        "school": ParagraphStyle(
            "school", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
            alignment=TA_LEFT, spaceAfter=0,
        ),
        "header_title": ParagraphStyle(
            "header_title", fontName="Helvetica-Bold", fontSize=20,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=0,
        ),
        "header_sub": ParagraphStyle(
            "header_sub", fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#90CAF9"), alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_MUTED, spaceBefore=12, spaceAfter=6,
            letterSpacing=1.2,
        ),
        "absent_name": ParagraphStyle(
            "absent_name", fontName="Helvetica-Bold", fontSize=13, textColor=TEXT,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10, textColor=TEXT,
        ),
        "small": ParagraphStyle(
            "small", fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
            alignment=TA_CENTER,
        ),
    }


# ── Header / Footer canvas callbacks ─────────────────────────────────────────

class _HeaderFooter:
    def __init__(self, day: str, date_str: str, total_pages: int):
        self.day = day
        self.date_str = date_str
        self.total_pages = total_pages

    def __call__(self, canv, doc):
        canv.saveState()
        w, h = A4

        # ── top header banner ──────────────────────────────────────────────
        header_h = 2.2 * cm
        canv.setFillColor(HEADER_BG)
        canv.rect(0, h - header_h, w, header_h, fill=1, stroke=0)

        # school name (left)
        canv.setFillColor(colors.HexColor("#90CAF9"))
        canv.setFont("Helvetica-Bold", 8)
        canv.drawString(L_MARGIN, h - 0.9 * cm, "BR SSS")

        # document title (center)
        canv.setFillColor(WHITE)
        canv.setFont("Helvetica-Bold", 15)
        title_text = "TEACHER REPLACEMENT SHEET"
        canv.drawCentredString(w / 2, h - 1.0 * cm, title_text)

        # date (right)
        canv.setFillColor(colors.HexColor("#90CAF9"))
        canv.setFont("Helvetica", 8)
        canv.drawRightString(w - R_MARGIN, h - 0.9 * cm, self.date_str)

        # day strip
        canv.setFillColor(PRIMARY)
        canv.rect(0, h - header_h - 0.55 * cm, w, 0.55 * cm, fill=1, stroke=0)
        canv.setFillColor(WHITE)
        canv.setFont("Helvetica-Bold", 9)
        canv.drawCentredString(w / 2, h - header_h - 0.40 * cm, f"Day:  {self.day}")

        # ── footer ─────────────────────────────────────────────────────────
        canv.setFillColor(BORDER)
        canv.rect(L_MARGIN, B_MARGIN - 0.3 * cm, w - L_MARGIN - R_MARGIN, 0.5,
                  fill=1, stroke=0)
        canv.setFillColor(TEXT_MUTED)
        canv.setFont("Helvetica", 7.5)
        canv.drawString(
            L_MARGIN, B_MARGIN - 0.7 * cm,
            f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}  ·  BR SSS Replacement System"
        )
        canv.drawRightString(
            w - R_MARGIN, B_MARGIN - 0.7 * cm,
            f"Page {doc.page}"
        )

        canv.restoreState()


# ── Main generator ────────────────────────────────────────────────────────────

def generate_pdf(session: dict, output_path: str) -> None:
    day          = session.get("day", "")
    absent_list  = session.get("absent_teachers", [])
    date_str     = datetime.now().strftime("%A, %d %B %Y")
    s            = _styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=T_MARGIN + 2.8 * cm,   # leave room for header
        bottomMargin=B_MARGIN + 0.5 * cm,
    )

    story = []

    # ── Section 1: Absent teachers ────────────────────────────────────────────
    story.append(Paragraph("ABSENT TEACHERS", s["section"]))

    absent_table_data = [
        [
            Paragraph("<b>#</b>", s["body"]),
            Paragraph("<b>Teacher Name</b>", s["body"]),
            Paragraph("<b>Periods Teaching</b>", s["body"]),
        ]
    ]
    for idx, teacher in enumerate(absent_list, 1):
        working = session["working_periods"].get(teacher, [])
        period_nums = ", ".join(str(p) for p, _ in working) if working else "None"
        absent_table_data.append([
            Paragraph(str(idx), s["body"]),
            Paragraph(f"<b>{teacher}</b>", s["absent_name"]),
            Paragraph(period_nums, s["body"]),
        ])

    absent_tbl = Table(
        absent_table_data,
        colWidths=[1.0 * cm, 7.0 * cm, None],
        hAlign="LEFT",
    )
    absent_tbl.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",  (0, 0), (-1, 0), LIGHT_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), PRIMARY),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        # Data rows
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("TOPPADDING",    (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        # Borders
        ("LINEBELOW",   (0, 0), (-1, 0), 1.5, PRIMARY),
        ("LINEBELOW",   (0, 1), (-1, -1), 0.5, BORDER),
        ("BOX",         (0, 0), (-1, -1), 1, BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(absent_tbl)
    story.append(Spacer(1, 0.6 * cm))

    # ── Section 2: Replacement schedule ──────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                             spaceAfter=8, spaceBefore=4))
    story.append(Paragraph("REPLACEMENT SCHEDULE", s["section"]))

    rows = logic.summary_rows(session)

    for teacher in absent_list:
        teacher_rows = [r for r in rows if r["absent"] == teacher]
        if not teacher_rows:
            continue

        teacher_block = []

        # teacher header
        teacher_header = Table(
            [[Paragraph(teacher, s["absent_name"])]],
            colWidths=[PAGE_W - L_MARGIN - R_MARGIN],
        )
        teacher_header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), DANGER_LT),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW",     (0, 0), (-1, -1), 1.5, DANGER),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        teacher_block.append(teacher_header)

        # detail rows table
        detail_data = [
            [
                Paragraph("<b>Period</b>", s["small"]),
                Paragraph("<b>Class / Subject</b>", s["small"]),
                Paragraph("<b>Room</b>", s["small"]),
                Paragraph("<b>Replaced By</b>", s["small"]),
            ]
        ]
        row_styles = []
        for i, r in enumerate(teacher_rows, 1):
            class_str, room_str = _split_class_room(r["class"])
            replacer  = r["replacer"]
            replacer_para = Paragraph(
                f"<b>{replacer}</b>" if replacer else "<i>— Unassigned —</i>",
                ParagraphStyle(
                    "rep", fontName="Helvetica-Bold" if replacer else "Helvetica-Oblique",
                    fontSize=10,
                    textColor=SUCCESS if replacer else WARNING,
                )
            )
            detail_data.append([
                Paragraph(f"Period {r['period']}", s["body"]),
                Paragraph(class_str or r["class"], s["body"]),
                Paragraph(room_str, s["small"]),
                replacer_para,
            ])
            if replacer:
                row_styles.append(("BACKGROUND", (3, i), (3, i), SUCCESS_LT))
            else:
                row_styles.append(("BACKGROUND", (3, i), (3, i), WARNING_LT))

        detail_tbl = Table(
            detail_data,
            colWidths=[2.0 * cm, 6.0 * cm, 3.5 * cm, None],
            hAlign="LEFT",
        )
        base_style = [
            # header row
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
            ("TEXTCOLOR",     (0, 0), (-1, 0), TEXT_MUTED),
            ("FONTSIZE",      (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING",    (0, 0), (-1, 0), 5),
            # data rows
            ("FONTSIZE",      (0, 1), (-1, -1), 10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, ROW_ALT]),
            ("TOPPADDING",    (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("LINEBELOW",     (0, 0), (-1, 0), 1, BORDER),
            ("LINEBELOW",     (0, 1), (-1, -1), 0.3, BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ]
        base_style.extend(row_styles)
        detail_tbl.setStyle(TableStyle(base_style))

        teacher_block.append(detail_tbl)
        teacher_block.append(Spacer(1, 0.35 * cm))

        story.append(KeepTogether(teacher_block))
        story.append(Spacer(1, 0.1 * cm))

    # ── Summary stats ─────────────────────────────────────────────────────────
    all_rows    = rows
    total       = len(all_rows)
    assigned    = sum(1 for r in all_rows if r["replacer"])
    unassigned  = total - assigned

    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                             spaceAfter=6))

    success_hex = SUCCESS.hexval()[2:]
    warning_hex = WARNING.hexval()[2:]
    stats_data = [[
        Paragraph(f"<b>Total periods to cover:</b>  {total}", s["body"]),
        Paragraph(
            f"<b>Assigned:</b>  <font color='#{success_hex}'>{assigned}</font>",
            s["body"]
        ),
        Paragraph(
            f"<b>Unassigned:</b>  <font color='#{warning_hex}'>{unassigned}</font>",
            s["body"]
        ) if unassigned else Paragraph(
            "<b>Unassigned:</b>  <font color='#2E7D32'>0 — All covered ✓</font>",
            s["body"]
        ),
    ]]
    stats_tbl = Table(stats_data, colWidths=["33%", "33%", "34%"])
    stats_tbl.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(stats_tbl)

    # build
    hf = _HeaderFooter(day, date_str, 0)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
