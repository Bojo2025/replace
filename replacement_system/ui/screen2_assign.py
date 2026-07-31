"""
Screen 2 – Assign replacements, one absent teacher at a time.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QProgressBar, QSizePolicy,
    QSpacerItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

from ui.styles import (
    C_PRIMARY, C_PRIMARY_LIGHT, C_ACCENT, C_TEXT, C_TEXT_MUTED,
    C_BG, C_CARD, C_BORDER, C_DANGER, C_DANGER_LIGHT,
    C_SUCCESS, C_SUCCESS_LIGHT, C_WARNING, C_WARNING_LIGHT,
)
import replacement_logic as logic


class PeriodRow(QFrame):
    """One row showing period number, class being taught, and replacement picker."""

    def __init__(self, period: int, class_label: str, free_teachers: list[str],
                 parent=None):
        super().__init__(parent)
        self.period = period
        self._free = free_teachers
        self.setObjectName("periodRowOuter")
        self.setStyleSheet(
            f"#periodRowOuter{{background:{C_CARD}; border:1px solid {C_BORDER}; "
            f"border-radius:10px; padding:2px;}}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._build(period, class_label, free_teachers)

    def _build(self, period: int, class_label: str, free_teachers: list[str]):
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        # Period badge
        badge = QLabel(f"P{period}")
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background:{C_PRIMARY}; color:white; border-radius:8px; "
            f"font-size:13px; font-weight:800;"
        )
        row.addWidget(badge)

        # Class info column
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        # Parse class / room from label (e.g. "13 ECO A 2.7")
        class_str, room_str = _split_class_room(class_label)

        cls_lbl = QLabel(class_str or class_label)
        cls_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:600;")
        info_col.addWidget(cls_lbl)

        if room_str:
            rm_lbl = QLabel(f"Room: {room_str}")
            rm_lbl.setStyleSheet(f"color:{C_TEXT_MUTED}; font-size:11px;")
            info_col.addWidget(rm_lbl)

        row.addLayout(info_col, stretch=1)

        # Replacement picker
        self._combo = QComboBox()
        self._combo.setMinimumWidth(260)
        self._combo.setMinimumHeight(36)
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.addItem("▾  Select replacement teacher…", None)
        for t in free_teachers:
            self._combo.addItem(f"  {t}", t)

        if not free_teachers:
            self._combo.clear()
            self._combo.addItem("  No free teachers this period", None)
            self._combo.setEnabled(False)
            self._combo.setToolTip("No free teachers available this period")

        # ── Force light colours on the combo and its popup ──────────────────
        # macOS dark mode ignores QSS on popups; QPalette is the reliable fix.
        _force_combo_light(self._combo)

        row.addWidget(self._combo)

        # Availability indicator
        self._avail_lbl = QLabel()
        self._avail_lbl.setFixedWidth(100)
        self._avail_lbl.setAlignment(Qt.AlignCenter)
        self._avail_lbl.setStyleSheet("font-size:11px; font-weight:600; border-radius:8px; padding:3px 6px;")
        row.addWidget(self._avail_lbl)

        self._update_avail_label(len(free_teachers))
        self._combo.currentIndexChanged.connect(self._on_combo_change)

    def _update_avail_label(self, count: int):
        if count == 0:
            self._avail_lbl.setText("None free")
            self._avail_lbl.setStyleSheet(
                f"font-size:11px; font-weight:600; border-radius:8px; padding:3px 6px; "
                f"background:{C_WARNING_LIGHT}; color:{C_WARNING};"
            )
        elif count <= 3:
            self._avail_lbl.setText(f"{count} available")
            self._avail_lbl.setStyleSheet(
                f"font-size:11px; font-weight:600; border-radius:8px; padding:3px 6px; "
                f"background:#FFF9C4; color:#F57F17;"
            )
        else:
            self._avail_lbl.setText(f"{count} available")
            self._avail_lbl.setStyleSheet(
                f"font-size:11px; font-weight:600; border-radius:8px; padding:3px 6px; "
                f"background:{C_SUCCESS_LIGHT}; color:{C_SUCCESS};"
            )

    def _on_combo_change(self, idx: int):
        if self._combo.currentData():
            self.setStyleSheet(
                f"#periodRowOuter{{background:{C_SUCCESS_LIGHT}; border:1px solid #A5D6A7; border-radius:10px; padding:2px;}}"
            )
        else:
            self.setStyleSheet(
                f"#periodRowOuter{{background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:10px; padding:2px;}}"
            )

    def get_selected_teacher(self) -> str | None:
        return self._combo.currentData()

    def set_teacher(self, teacher: str | None):
        if not teacher:
            self._combo.setCurrentIndex(0)
            return
        idx = self._combo.findData(teacher)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)


# ── Screen 2 ─────────────────────────────────────────────────────────────────

class Screen2(QWidget):
    """
    Signals:
        go_back()
        proceed(session)   – session dict with all assignments
    """
    go_back = pyqtSignal()
    proceed = pyqtSignal(dict)

    def __init__(self, schedules, parent=None):
        super().__init__(parent)
        self.schedules = schedules
        self._session: dict = {}
        self._teacher_idx: int = 0
        self._period_rows: dict[int, PeriodRow] = {}
        self._build_ui()

    # ── construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── header info ───────────────────────────────────────────────────────
        hdr = QHBoxLayout()

        self._teacher_chip = QLabel()
        self._teacher_chip.setStyleSheet(
            f"background:{C_DANGER_LIGHT}; color:{C_DANGER}; "
            f"border-radius:10px; padding:5px 14px; font-size:13px; font-weight:700;"
        )
        hdr.addWidget(self._teacher_chip)
        hdr.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed))

        self._day_chip = QLabel()
        self._day_chip.setStyleSheet(
            f"background:{C_PRIMARY_LIGHT}; color:{C_PRIMARY}; "
            f"border-radius:10px; padding:5px 14px; font-size:13px; font-weight:600;"
        )
        hdr.addWidget(self._day_chip)
        hdr.addStretch()

        self._progress_lbl = QLabel()
        self._progress_lbl.setStyleSheet(f"color:{C_TEXT_MUTED}; font-size:12px;")
        hdr.addWidget(self._progress_lbl)

        root.addLayout(hdr)

        # progress bar
        self._prog_bar = QProgressBar()
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setFixedHeight(6)
        root.addWidget(self._prog_bar)

        # ── title ─────────────────────────────────────────────────────────────
        self._title_lbl = QLabel()
        self._title_lbl.setFont(QFont("", 15, QFont.Bold))
        self._title_lbl.setStyleSheet(f"color:{C_TEXT};")
        root.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel()
        self._subtitle_lbl.setStyleSheet(f"color:{C_TEXT_MUTED}; font-size:12px;")
        root.addWidget(self._subtitle_lbl)

        # ── period rows area ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;}")

        self._scroll_contents = QWidget()
        self._scroll_contents.setStyleSheet("background:transparent;")
        self._rows_layout = QVBoxLayout(self._scroll_contents)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(10)
        self._rows_layout.addStretch()

        scroll.setWidget(self._scroll_contents)
        root.addWidget(scroll, stretch=1)

        # ── action bar ────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        root.addWidget(sep)

        action = QHBoxLayout()
        action.setSpacing(12)

        self._back_btn = QPushButton("← Back")
        self._back_btn.setObjectName("secondaryBtn")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFixedHeight(42)
        self._back_btn.setMinimumWidth(100)
        self._back_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #1565C0; border: 2px solid #1565C0; "
            "border-radius: 8px; padding: 9px 24px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #E3F2FD; }"
        )
        self._back_btn.clicked.connect(self._on_back)
        action.addWidget(self._back_btn)

        action.addStretch()

        self._warn_lbl = QLabel()
        self._warn_lbl.setStyleSheet(f"color:{C_WARNING}; font-size:12px;")
        action.addWidget(self._warn_lbl)

        self._next_btn = QPushButton()
        self._next_btn.setObjectName("primaryBtn")
        self._next_btn.setFixedHeight(42)
        self._next_btn.setMinimumWidth(160)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 10px 28px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #0D47A1; }"
            "QPushButton:pressed { background-color: #082d7a; }"
        )
        self._next_btn.clicked.connect(self._on_next)
        action.addWidget(self._next_btn)

        root.addLayout(action)

    # ── public API ────────────────────────────────────────────────────────────

    def load_session(self, session: dict):
        """Called by the main window when entering Screen 2."""
        self._session = session
        self._teacher_idx = 0
        self._show_teacher(0)

    # ── internal ─────────────────────────────────────────────────────────────

    def _current_teacher(self) -> str:
        return self._session["absent_teachers"][self._teacher_idx]

    def _show_teacher(self, idx: int):
        self._teacher_idx = idx
        teacher = self._current_teacher()
        total   = len(self._session["absent_teachers"])
        day     = self._session["day"]

        self._teacher_chip.setText(f"  {teacher}  ")
        self._day_chip.setText(f"  {day}  ")
        self._progress_lbl.setText(f"Teacher {idx + 1} of {total}")
        self._prog_bar.setMaximum(total)
        self._prog_bar.setValue(idx + 1)

        self._title_lbl.setText(f"Assign replacements for {teacher}")

        working = self._session["working_periods"].get(teacher, [])
        if working:
            self._subtitle_lbl.setText(
                f"This teacher has {len(working)} teaching period(s) on {day}. "
                f"Select a free teacher for each one."
            )
        else:
            self._subtitle_lbl.setText(
                f"{teacher} has no teaching periods on {day} – nothing to assign."
            )

        self._next_btn.setText(
            "Review Summary  →" if idx == total - 1 else "Next Teacher  →"
        )

        self._rebuild_rows(teacher, day)

    def _rebuild_rows(self, teacher: str, day: str):
        # Clear existing rows
        self._period_rows.clear()
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        working = self._session["working_periods"].get(teacher, [])

        if not working:
            empty_lbl = QLabel("✓  No teaching periods — skip to the next teacher.")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet(
                f"color:{C_TEXT_MUTED}; font-size:14px; padding:40px;"
            )
            self._rows_layout.insertWidget(0, empty_lbl)
            return

        for period, class_label in working:
            exclude = set(self._session["absent_teachers"])
            # also exclude teachers already assigned to this period for others
            for other_t, assigns in self._session["assignments"].items():
                if other_t == teacher:
                    continue
                r = assigns.get(period)
                if r:
                    exclude.add(r)

            free = logic.available_replacements(
                self.schedules, self._session, teacher, period
            )

            row_widget = PeriodRow(period, class_label, free)
            # Restore previous selection if user navigated back
            prev = self._session["assignments"].get(teacher, {}).get(period)
            if prev:
                row_widget.set_teacher(prev)

            self._period_rows[period] = row_widget
            self._rows_layout.insertWidget(
                self._rows_layout.count() - 1, row_widget
            )

    def _save_current_assignments(self):
        teacher = self._current_teacher()
        for period, row_widget in self._period_rows.items():
            selected = row_widget.get_selected_teacher()
            logic.assign_replacement(self._session, teacher, period, selected)

    def _on_back(self):
        self._save_current_assignments()
        if self._teacher_idx > 0:
            self._show_teacher(self._teacher_idx - 1)
        else:
            self.go_back.emit()

    def _on_next(self):
        self._save_current_assignments()
        self._warn_lbl.setText("")
        total = len(self._session["absent_teachers"])

        if self._teacher_idx < total - 1:
            self._show_teacher(self._teacher_idx + 1)
        else:
            self.proceed.emit(self._session)


# ── helpers ───────────────────────────────────────────────────────────────────

def _force_combo_light(combo: QComboBox) -> None:
    """
    Force white background + dark text on a QComboBox AND its dropdown popup.
    Needed on macOS where dark-mode overrides QSS colours on popup lists.
    """
    WHITE      = QColor("#FFFFFF")
    DARK_TEXT  = QColor("#1E293B")
    HIGHLIGHT  = QColor("#DBEAFE")
    MUTED      = QColor("#64748B")
    BORDER_COL = QColor("#1565C0")

    # ── Combo box itself ──────────────────────────────────────────────────────
    pal = QPalette()
    pal.setColor(QPalette.Base,            WHITE)
    pal.setColor(QPalette.Background,      WHITE)
    pal.setColor(QPalette.Window,          WHITE)
    pal.setColor(QPalette.WindowText,      DARK_TEXT)
    pal.setColor(QPalette.Text,            DARK_TEXT)
    pal.setColor(QPalette.ButtonText,      DARK_TEXT)
    pal.setColor(QPalette.Highlight,       HIGHLIGHT)
    pal.setColor(QPalette.HighlightedText, DARK_TEXT)
    combo.setPalette(pal)

    combo.setStyleSheet(
        "QComboBox {"
        "  background-color: #FFFFFF;"
        "  color: #1E293B;"
        "  border: 2px solid #1565C0;"
        "  border-radius: 8px;"
        "  padding: 6px 32px 6px 12px;"
        "  font-size: 13px;"
        "  min-width: 250px;"
        "  min-height: 34px;"
        "}"
        "QComboBox:hover { border-color: #1E88E5; background-color: #EFF6FF; }"
        "QComboBox:disabled {"
        "  background-color: #F1F5F9; color: #94A3B8; border-color: #CBD5E1;"
        "}"
        "QComboBox::drop-down {"
        "  width: 30px;"
        "  border-left: 1px solid #CBD5E1;"
        "  border-top-right-radius: 7px;"
        "  border-bottom-right-radius: 7px;"
        "  background: #EFF6FF;"
        "}"
        "QComboBox::down-arrow {"
        "  width: 0; height: 0;"
        "  border-left: 5px solid transparent;"
        "  border-right: 5px solid transparent;"
        "  border-top: 6px solid #1565C0;"
        "}"
    )

    # ── Popup list view ───────────────────────────────────────────────────────
    view = combo.view()
    view_pal = QPalette()
    view_pal.setColor(QPalette.Base,            WHITE)
    view_pal.setColor(QPalette.Background,      WHITE)
    view_pal.setColor(QPalette.Window,          WHITE)
    view_pal.setColor(QPalette.WindowText,      DARK_TEXT)
    view_pal.setColor(QPalette.Text,            DARK_TEXT)
    view_pal.setColor(QPalette.Highlight,       HIGHLIGHT)
    view_pal.setColor(QPalette.HighlightedText, DARK_TEXT)
    view.setPalette(view_pal)
    view.setAutoFillBackground(True)

    view.setStyleSheet(
        "QListView {"
        "  background-color: #FFFFFF;"
        "  color: #1E293B;"
        "  border: 1px solid #CBD5E1;"
        "  outline: none;"
        "}"
        "QListView::item {"
        "  background-color: #FFFFFF;"
        "  color: #1E293B;"
        "  padding: 8px 14px;"
        "  min-height: 28px;"
        "}"
        "QListView::item:hover {"
        "  background-color: #DBEAFE;"
        "  color: #1E293B;"
        "}"
        "QListView::item:selected {"
        "  background-color: #BFDBFE;"
        "  color: #1E293B;"
        "}"
    )


def _split_class_room(label: str) -> tuple[str, str]:
    """
    Try to separate the class name from the room code.
    Room codes look like: A 2.7, B 1.9, Chem L 1, C Bio 2, playground, etc.
    Returns (class_part, room_part).
    """
    import re
    # Known room-code patterns at the end of the string
    room_pattern = re.compile(
        r"\s+([AB]\s*\d+\.\d+\w*"
        r"|Chem\s+L\s*\d*"
        r"|C\s+(?:Phy|Bio|Com|WK|PE|Hindi|Hin)\s*\d*"
        r"|A\s+Urdu\s+Rm"
        r"|CDT\s*\d*"
        r"|playground\s*\d*"
        r"|Library\s+Rm"
        r"|Audio"
        r"|BIO/MUSIC"
        r"|B\s+\d+\.\d+\w*)"
        r"\s*$",
        re.IGNORECASE,
    )
    m = room_pattern.search(label)
    if m:
        return label[:m.start()].strip(), label[m.start():].strip()
    return label.strip(), ""
