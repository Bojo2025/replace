"""
Screen 1 – Select the day and the absent teachers.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QCheckBox, QFrame, QSizePolicy,
    QSpacerItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.styles import (
    C_PRIMARY, C_TEXT, C_TEXT_MUTED, C_BG, C_CARD, C_BORDER,
    C_DANGER, C_DANGER_LIGHT, C_SUCCESS, C_SUCCESS_LIGHT,
    C_PRIMARY_LIGHT,
)
import data_loader


class Screen1(QWidget):
    """
    Signals:
        proceed(day: str, absent: list[str])  – emitted when user clicks Next
    """
    proceed = pyqtSignal(str, list)

    def __init__(self, schedules: dict, teacher_order: list, parent=None):
        super().__init__(parent)
        self.schedules = schedules
        self.teacher_order = teacher_order
        self.selected_day = "Monday"
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    # ── construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── page title ────────────────────────────────────────────────────────
        title = QLabel("New Replacement Sheet")
        title.setFont(QFont("", 19, QFont.Bold))
        title.setStyleSheet(f"color:{C_TEXT};")
        subtitle = QLabel("Select the day, then mark all absent teachers for that day.")
        subtitle.setStyleSheet(f"color:{C_TEXT_MUTED}; font-size:13px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        # ── Day selector card ─────────────────────────────────────────────────
        day_card = self._make_card()
        day_layout = QVBoxLayout(day_card)
        day_layout.setContentsMargins(20, 16, 20, 16)
        day_layout.setSpacing(12)

        day_lbl = QLabel("SELECT DAY")
        day_lbl.setObjectName("sectionLabel")
        day_layout.addWidget(day_lbl)

        self._day_btn_row = QHBoxLayout()
        self._day_btn_row.setSpacing(10)
        self._day_buttons: dict[str, QPushButton] = {}
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            btn = QPushButton(d)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, day=d: self._select_day(day))
            self._day_buttons[d] = btn
            self._day_btn_row.addWidget(btn)
        self._day_btn_row.addStretch()
        day_layout.addLayout(self._day_btn_row)

        root.addWidget(day_card)
        self.selected_day = "Monday"
        self._apply_day_button_styles("Monday")

        # ── Teacher list card ─────────────────────────────────────────────────
        teacher_card = self._make_card()
        tc_layout = QVBoxLayout(teacher_card)
        tc_layout.setContentsMargins(20, 16, 20, 16)
        tc_layout.setSpacing(12)

        tc_header = QHBoxLayout()
        tc_lbl = QLabel("ABSENT TEACHERS")
        tc_lbl.setObjectName("sectionLabel")
        tc_header.addWidget(tc_lbl)
        tc_header.addStretch()

        self._count_badge = QLabel("0 selected")
        self._count_badge.setStyleSheet(
            f"background:{C_PRIMARY_LIGHT}; color:{C_PRIMARY}; "
            f"border-radius:10px; padding:3px 12px; font-size:12px; font-weight:600;"
        )
        tc_header.addWidget(self._count_badge)
        tc_layout.addLayout(tc_header)

        # search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search teacher…")
        self._search.textChanged.connect(self._filter_teachers)
        tc_layout.addWidget(self._search)

        # select all / clear row
        sa_row = QHBoxLayout()
        sa_row.setSpacing(6)
        btn_all = QPushButton("Select All")
        btn_all.setObjectName("ghostBtn")
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_all.setFixedHeight(30)
        btn_all.clicked.connect(self._select_all)

        btn_none = QPushButton("Clear All")
        btn_none.setObjectName("ghostBtn")
        btn_none.setCursor(Qt.PointingHandCursor)
        btn_none.setFixedHeight(30)
        btn_none.clicked.connect(self._clear_all)

        sa_row.addWidget(btn_all)
        sa_row.addWidget(btn_none)
        sa_row.addStretch()
        tc_layout.addLayout(sa_row)

        # scrollable checkbox list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;}")
        scroll.setMinimumHeight(280)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background:transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(4)
        self._rebuild_teacher_list()

        scroll.setWidget(self._list_widget)
        tc_layout.addWidget(scroll)

        root.addWidget(teacher_card)

        # ── bottom action bar ─────────────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self._warn_label = QLabel("")
        self._warn_label.setStyleSheet(f"color:{C_DANGER}; font-size:12px;")
        bottom.addWidget(self._warn_label)
        bottom.addStretch()

        self._next_btn = QPushButton("Next  →")
        self._next_btn.setObjectName("primaryBtn")
        self._next_btn.setFixedHeight(42)
        self._next_btn.setMinimumWidth(130)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 10px 28px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #0D47A1; }"
            "QPushButton:pressed { background-color: #082d7a; }"
        )
        self._next_btn.clicked.connect(self._on_next)
        bottom.addWidget(self._next_btn)

        root.addLayout(bottom)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            f"#card{{background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:10px;}}"
        )
        return card

    def _teachers_for_selected_day(self) -> list[str]:
        """Teachers who work on the currently selected day (full-time / MWF / Tue–Thu)."""
        return [
            t for t in self.teacher_order
            if self.selected_day in data_loader.replacement_working_days(self.schedules, t)
        ]

    def _rebuild_teacher_list(self):
        """Rebuild checkbox list for the current day (part-time teachers omitted)."""
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()
        for teacher in self._teachers_for_selected_day():
            cb = QCheckBox(teacher)
            cb.setStyleSheet(
                f"QCheckBox{{padding:5px 6px; border-radius:6px;}}"
                f"QCheckBox:hover{{background:{C_PRIMARY_LIGHT};}}"
            )
            cb.stateChanged.connect(self._update_count)
            self._checkboxes[teacher] = cb
            self._list_layout.addWidget(cb)
        self._list_layout.addStretch()

    def _apply_day_button_styles(self, day: str):
        for d, btn in self._day_buttons.items():
            if d == day:
                btn.setObjectName("dayBtnActive")
                btn.setStyleSheet(
                    f"background:{C_PRIMARY}; color:white; border:2px solid {C_PRIMARY}; "
                    f"border-radius:8px; padding:9px 18px; font-size:13px; font-weight:700; min-width:100px;"
                )
            else:
                btn.setObjectName("dayBtn")
                btn.setStyleSheet(
                    f"background:{C_CARD}; color:{C_TEXT_MUTED}; border:2px solid {C_BORDER}; "
                    f"border-radius:8px; padding:9px 18px; font-size:13px; min-width:100px;"
                )
            btn.setCursor(Qt.PointingHandCursor)

    def _select_day(self, day: str):
        self.selected_day = day
        self._apply_day_button_styles(day)
        self._rebuild_teacher_list()
        self._filter_teachers(self._search.text())
        self._update_count()

    def _filter_teachers(self, text: str):
        term = text.strip().lower()
        for teacher, cb in self._checkboxes.items():
            cb.setVisible(term == "" or term in teacher.lower())

    def _select_all(self):
        for teacher, cb in self._checkboxes.items():
            if cb.isVisible():
                cb.setChecked(True)

    def _clear_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _update_count(self):
        count = sum(1 for cb in self._checkboxes.values() if cb.isChecked())
        if count == 0:
            self._count_badge.setText("0 selected")
            self._count_badge.setStyleSheet(
                f"background:{C_PRIMARY_LIGHT}; color:{C_PRIMARY}; "
                f"border-radius:10px; padding:3px 12px; font-size:12px; font-weight:600;"
            )
        else:
            self._count_badge.setText(f"{count} absent")
            self._count_badge.setStyleSheet(
                f"background:{C_DANGER_LIGHT}; color:{C_DANGER}; "
                f"border-radius:10px; padding:3px 12px; font-size:12px; font-weight:600;"
            )
        self._warn_label.setText("")

    def _on_next(self):
        absent = [t for t, cb in self._checkboxes.items() if cb.isChecked()]
        if not absent:
            self._warn_label.setText("⚠  Please select at least one absent teacher.")
            return
        self.proceed.emit(self.selected_day, absent)

    # ── public ────────────────────────────────────────────────────────────────

    def reset(self):
        """Reset the form to default state."""
        self._search.clear()
        self._select_day("Monday")
        self._warn_label.setText("")
