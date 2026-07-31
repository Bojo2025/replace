"""
Centralised stylesheet and colour constants for the replacement system UI.
"""

# ── Palette ──────────────────────────────────────────────────────────────────
C_PRIMARY       = "#1565C0"   # deep blue  – buttons, header accents
C_PRIMARY_DARK  = "#0D47A1"   # hover state
C_PRIMARY_LIGHT = "#E3F2FD"   # selection background
C_ACCENT        = "#1E88E5"   # lighter blue – secondary elements
C_BG            = "#F0F4F8"   # app background
C_CARD          = "#FFFFFF"   # card / panel background
C_BORDER        = "#CBD5E1"   # subtle borders
C_TEXT          = "#1E293B"   # primary text
C_TEXT_MUTED    = "#64748B"   # secondary / label text
C_SUCCESS       = "#2E7D32"   # green  – available / assigned
C_SUCCESS_LIGHT = "#E8F5E9"
C_DANGER        = "#C62828"   # red    – absent
C_DANGER_LIGHT  = "#FFEBEE"
C_WARNING       = "#E65100"   # orange – unassigned warning
C_WARNING_LIGHT = "#FFF3E0"
C_HEADER_BG     = "#1A237E"   # app header bar
C_HEADER_TEXT   = "#FFFFFF"
C_STEP_ACTIVE   = "#1E88E5"
C_STEP_DONE     = "#43A047"
C_STEP_PENDING  = "#B0BEC5"

FONT_FAMILY = "Segoe UI, SF Pro Display, Helvetica Neue, Arial, sans-serif"

# ── Global QSS ───────────────────────────────────────────────────────────────
GLOBAL_STYLE = f"""
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {C_TEXT};
    background-color: {C_BG};
}}

/* ── Header bar ── */
#headerBar {{
    background-color: {C_HEADER_BG};
    padding: 0px;
}}
#headerTitle {{
    color: {C_HEADER_TEXT};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
#headerSubtitle {{
    color: rgba(255,255,255,0.70);
    font-size: 12px;
}}

/* ── Step indicator ── */
#stepBar {{
    background-color: {C_PRIMARY_DARK};
    padding: 8px 0px;
}}
#stepLabel {{
    color: rgba(255,255,255,0.55);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.8px;
}}
#stepLabelActive {{
    color: {C_HEADER_TEXT};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
}}

/* ── Card ── */
#card {{
    background-color: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
}}
#cardTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {C_TEXT};
}}
#sectionLabel {{
    font-size: 11px;
    font-weight: 600;
    color: {C_TEXT_MUTED};
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

/* ── Primary button ── */
QPushButton#primaryBtn {{
    background-color: {C_PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#primaryBtn:hover {{
    background-color: {C_PRIMARY_DARK};
}}
QPushButton#primaryBtn:pressed {{
    background-color: #082d7a;
}}
QPushButton#primaryBtn:disabled {{
    background-color: {C_STEP_PENDING};
    color: #90A4AE;
}}

/* ── Secondary button ── */
QPushButton#secondaryBtn {{
    background-color: transparent;
    color: {C_PRIMARY};
    border: 2px solid {C_PRIMARY};
    border-radius: 8px;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#secondaryBtn:hover {{
    background-color: {C_PRIMARY_LIGHT};
}}
QPushButton#secondaryBtn:pressed {{
    background-color: #BBDEFB;
}}

/* ── Danger button ── */
QPushButton#dangerBtn {{
    background-color: {C_DANGER};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#dangerBtn:hover {{
    background-color: #B71C1C;
}}

/* ── Ghost button ── */
QPushButton#ghostBtn {{
    background-color: transparent;
    color: {C_TEXT_MUTED};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
}}
QPushButton#ghostBtn:hover {{
    background-color: #EEF2F7;
    color: {C_TEXT};
}}

/* ── Search / line-edit ── */
QLineEdit {{
    background-color: {C_CARD};
    border: 1.5px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: {C_TEXT};
    selection-background-color: {C_PRIMARY_LIGHT};
}}
QLineEdit:focus {{
    border-color: {C_ACCENT};
}}

/* ── List widget ── */
QListWidget {{
    background-color: {C_CARD};
    border: 1.5px solid {C_BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 2px;
}}
QListWidget::item:hover {{
    background-color: {C_PRIMARY_LIGHT};
}}
QListWidget::item:selected {{
    background-color: #BBDEFB;
    color: {C_TEXT};
}}

/* QComboBox is styled inline via _force_combo_light() in screen2_assign.py */

/* ── Scroll bars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {C_BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Progress bar ── */
QProgressBar {{
    background-color: #E2E8F0;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    border: none;
}}
QProgressBar::chunk {{
    background-color: {C_ACCENT};
    border-radius: 4px;
}}

/* ── Checkboxes ── */
QCheckBox {{
    spacing: 8px;
    color: {C_TEXT};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {C_BORDER};
    border-radius: 4px;
    background: {C_CARD};
}}
QCheckBox::indicator:checked {{
    background-color: {C_PRIMARY};
    border-color: {C_PRIMARY};
}}
QCheckBox::indicator:hover {{
    border-color: {C_ACCENT};
}}

/* ── Day-select radio buttons ── */
QPushButton#dayBtn {{
    background-color: {C_CARD};
    color: {C_TEXT_MUTED};
    border: 2px solid {C_BORDER};
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 500;
    min-width: 100px;
}}
QPushButton#dayBtn:hover {{
    border-color: {C_ACCENT};
    color: {C_ACCENT};
    background-color: {C_PRIMARY_LIGHT};
}}
QPushButton#dayBtnActive {{
    background-color: {C_PRIMARY};
    color: white;
    border: 2px solid {C_PRIMARY};
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 700;
    min-width: 100px;
}}

/* ── Period row (screen 2) ── */
#periodRow {{
    background-color: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 4px;
}}
#periodRow:hover {{
    border-color: {C_ACCENT};
}}
#periodBadge {{
    background-color: {C_PRIMARY};
    color: white;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 8px;
    min-width: 26px;
}}
#classLabel {{
    color: {C_TEXT};
    font-size: 13px;
    font-weight: 500;
}}
#roomLabel {{
    color: {C_TEXT_MUTED};
    font-size: 11px;
}}

/* ── Summary table ── */
#summaryTable {{
    background-color: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
}}
QTableWidget {{
    background-color: {C_CARD};
    border: none;
    gridline-color: {C_BORDER};
    selection-background-color: {C_PRIMARY_LIGHT};
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
}}
QHeaderView::section {{
    background-color: #EEF2F7;
    color: {C_TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 8px 12px;
    border: none;
    border-right: 1px solid {C_BORDER};
    border-bottom: 1px solid {C_BORDER};
}}

/* ── Absent teacher chip ── */
#absentChip {{
    background-color: {C_DANGER_LIGHT};
    color: {C_DANGER};
    border: 1px solid #FFCDD2;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: {C_TEXT};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}}
"""


def badge_style(color_bg: str, color_text: str) -> str:
    return (
        f"background-color:{color_bg}; color:{color_text}; "
        f"border-radius:10px; padding:3px 10px; "
        f"font-size:11px; font-weight:600;"
    )
