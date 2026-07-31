"""
Screen 3 – Review summary and generate the replacement PDF.
"""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QScrollArea, QSizePolicy, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

from ui.styles import (
    C_PRIMARY, C_PRIMARY_LIGHT, C_TEXT, C_TEXT_MUTED, C_BG, C_CARD, C_BORDER,
    C_DANGER, C_DANGER_LIGHT, C_SUCCESS, C_SUCCESS_LIGHT, C_WARNING, C_WARNING_LIGHT,
)
import replacement_logic as logic
import pdf_generator


class Screen3(QWidget):
    """
    Signals:
        go_back()          – user wants to go back and edit
        start_over()       – user clicks "New Sheet"
    """
    go_back   = pyqtSignal()
    start_over = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session: dict = {}
        self._build_ui()

    # ── construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── page title ────────────────────────────────────────────────────────
        title = QLabel("Review Replacement Sheet")
        title.setFont(QFont("", 19, QFont.Bold))
        title.setStyleSheet(f"color:{C_TEXT};")
        root.addWidget(title)

        self._subtitle = QLabel()
        self._subtitle.setStyleSheet(f"color:{C_TEXT_MUTED}; font-size:13px;")
        root.addWidget(self._subtitle)

        # ── absent-teacher chips ──────────────────────────────────────────────
        self._chips_row = QHBoxLayout()
        self._chips_row.setSpacing(8)
        self._chips_row.addStretch()
        root.addLayout(self._chips_row)

        # ── table card ────────────────────────────────────────────────────────
        tcard = QFrame()
        tcard.setStyleSheet(
            f"QFrame{{background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:10px;}}"
        )
        tcard_layout = QVBoxLayout(tcard)
        tcard_layout.setContentsMargins(0, 0, 0, 0)
        tcard_layout.setSpacing(0)

        # table header row
        th_row = QHBoxLayout()
        th_row.setContentsMargins(20, 14, 20, 10)
        table_title = QLabel("REPLACEMENT SCHEDULE")
        table_title.setObjectName("sectionLabel")
        th_row.addWidget(table_title)
        th_row.addStretch()

        self._unassigned_badge = QLabel()
        th_row.addWidget(self._unassigned_badge)
        tcard_layout.addLayout(th_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        tcard_layout.addWidget(sep)

        # table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Absent Teacher", "Period", "Class / Subject", "Room", "Replaced By"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            f"QTableWidget{{background:{C_CARD}; alternate-background-color:#F8FAFC; border:none;}}"
            f"QTableWidget::item{{padding:8px 12px; border-bottom:1px solid #F1F5F9;}}"
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed);  self._table.setColumnWidth(1, 70)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed);  self._table.setColumnWidth(3, 130)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setFrameShape(QFrame.NoFrame)
        tcard_layout.addWidget(self._table)

        root.addWidget(tcard, stretch=1)

        # ── action bar ────────────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{C_BORDER};")
        root.addWidget(sep2)

        action = QHBoxLayout()
        action.setSpacing(12)

        self._back_btn = QPushButton("← Edit Assignments")
        self._back_btn.setObjectName("secondaryBtn")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFixedHeight(42)
        self._back_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #1565C0; border: 2px solid #1565C0; "
            "border-radius: 8px; padding: 9px 24px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #E3F2FD; }"
        )
        self._back_btn.clicked.connect(self.go_back.emit)
        action.addWidget(self._back_btn)

        action.addStretch()

        self._new_btn = QPushButton("New Sheet")
        self._new_btn.setObjectName("ghostBtn")
        self._new_btn.setCursor(Qt.PointingHandCursor)
        self._new_btn.setFixedHeight(42)
        self._new_btn.setMinimumWidth(110)
        self._new_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #64748B; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 9px 20px; font-size: 13px; }"
            "QPushButton:hover { background-color: #F1F5F9; color: #1E293B; }"
        )
        self._new_btn.clicked.connect(self.start_over.emit)
        action.addWidget(self._new_btn)

        self._pdf_btn = QPushButton("  Generate PDF  ")
        self._pdf_btn.setObjectName("primaryBtn")
        self._pdf_btn.setFixedHeight(42)
        self._pdf_btn.setMinimumWidth(170)
        self._pdf_btn.setCursor(Qt.PointingHandCursor)
        self._pdf_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 10px 28px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #0D47A1; }"
            "QPushButton:pressed { background-color: #082d7a; }"
        )
        self._pdf_btn.clicked.connect(self._on_generate_pdf)
        action.addWidget(self._pdf_btn)

        root.addLayout(action)

        # status message
        self._status_lbl = QLabel()
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet("font-size:12px; padding:4px 0;")
        root.addWidget(self._status_lbl)

    # ── public API ────────────────────────────────────────────────────────────

    def load_session(self, session: dict):
        self._session = session
        self._status_lbl.setText("")
        self._refresh_view()

    # ── internal ─────────────────────────────────────────────────────────────

    def _refresh_view(self):
        day     = self._session.get("day", "")
        absent  = self._session.get("absent_teachers", [])

        self._subtitle.setText(
            f"Day: {day}  ·  {len(absent)} absent teacher(s)  ·  "
            f"Review below and generate the PDF when ready."
        )

        # chips
        for i in reversed(range(self._chips_row.count())):
            item = self._chips_row.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._chips_row.addStretch()
        for t in absent:
            chip = QLabel(f"  {t}  ")
            chip.setStyleSheet(
                f"background:{C_DANGER_LIGHT}; color:{C_DANGER}; "
                f"border-radius:10px; padding:4px 12px; font-size:12px; font-weight:600;"
            )
            self._chips_row.addWidget(chip)

        # table
        rows = logic.summary_rows(self._session)
        unassigned = sum(1 for r in rows if not r["replacer"])

        if unassigned:
            self._unassigned_badge.setText(f"⚠  {unassigned} unassigned")
            self._unassigned_badge.setStyleSheet(
                f"background:{C_WARNING_LIGHT}; color:{C_WARNING}; "
                f"border-radius:8px; padding:3px 10px; font-size:11px; font-weight:600;"
            )
        else:
            self._unassigned_badge.setText("✓  All assigned")
            self._unassigned_badge.setStyleSheet(
                f"background:{C_SUCCESS_LIGHT}; color:{C_SUCCESS}; "
                f"border-radius:8px; padding:3px 10px; font-size:11px; font-weight:600;"
            )

        self._table.setRowCount(0)
        prev_absent = None

        from ui.screen2_assign import _split_class_room

        for r in rows:
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)

            absent_name = r["absent"]
            show_name   = "" if absent_name == prev_absent else absent_name
            prev_absent = absent_name

            class_str, room_str = _split_class_room(r["class"])

            cells = [
                (show_name, C_TEXT if show_name else C_TEXT_MUTED),
                (f"Period {r['period']}", C_TEXT),
                (class_str or r["class"], C_TEXT),
                (room_str, C_TEXT_MUTED),
                (r["replacer"] or "— Unassigned —",
                 C_SUCCESS if r["replacer"] else C_WARNING),
            ]

            for col, (text, color) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setForeground(QBrush(QColor(color)))
                if col == 4 and not r["replacer"]:
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                if col == 0 and show_name:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self._table.setItem(row_idx, col, item)

        self._table.resizeRowsToContents()

    def _on_generate_pdf(self):
        day     = self._session.get("day", "day")
        date_str = datetime.now().strftime("%Y-%m-%d")
        default_name = f"Replacement_{day}_{date_str}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Replacement PDF", default_name,
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            pdf_generator.generate_pdf(self._session, path)
            self._status_lbl.setText(
                f"✅  PDF saved to: {os.path.basename(path)}"
            )
            self._status_lbl.setStyleSheet(
                f"color:{C_SUCCESS}; font-size:12px; padding:4px 0; font-weight:600;"
            )
            # Try to open the PDF automatically
            self._open_pdf(path)
        except Exception as exc:
            self._status_lbl.setText(f"❌  Error: {exc}")
            self._status_lbl.setStyleSheet(
                f"color:{C_DANGER}; font-size:12px; padding:4px 0;"
            )

    @staticmethod
    def _open_pdf(path: str):
        import subprocess, sys
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
