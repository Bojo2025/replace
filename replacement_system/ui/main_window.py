"""
Main application window – persistent header + step indicator + stacked pages.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.styles import (
    C_HEADER_BG, C_HEADER_TEXT, C_PRIMARY, C_PRIMARY_DARK,
    C_STEP_ACTIVE, C_STEP_DONE, C_STEP_PENDING, C_BG, C_BORDER, C_CARD,
    C_TEXT_MUTED,
)
from ui.screen1_select import Screen1
from ui.screen2_assign import Screen2
from ui.screen3_review import Screen3
import replacement_logic as logic


STEPS = ["① Select Day & Teachers", "② Assign Replacements", "③ Review & Export"]


class MainWindow(QMainWindow):
    def __init__(self, schedules, teacher_order):
        super().__init__()
        self.schedules      = schedules
        self.teacher_order  = teacher_order
        self._session: dict = {}

        self.setWindowTitle("BR SSS — Teacher Replacement System")
        self.setMinimumSize(960, 700)
        self.resize(1050, 760)

        self._build_ui()

    # ── construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background:{C_BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header bar ────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(64)
        header.setStyleSheet(f"background:{C_HEADER_BG};")
        hdr_lay = QHBoxLayout(header)
        hdr_lay.setContentsMargins(28, 0, 28, 0)
        hdr_lay.setSpacing(10)

        # logo circle placeholder
        logo = QLabel("BR")
        logo.setFixedSize(38, 38)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "background:rgba(255,255,255,0.15); color:white; border-radius:19px; "
            "font-size:13px; font-weight:800; border:2px solid rgba(255,255,255,0.3);"
        )
        hdr_lay.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_lbl = QLabel("BR SSS — Teacher Replacement System")
        title_lbl.setStyleSheet("color:white; font-size:15px; font-weight:700;")
        subtitle_lbl = QLabel("Timetable: latest 20 april.xlsx")
        subtitle_lbl.setStyleSheet("color:rgba(255,255,255,0.60); font-size:11px;")
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)
        hdr_lay.addLayout(title_col)
        hdr_lay.addStretch()

        # day badge (updated when session starts)
        self._day_badge = QLabel()
        self._day_badge.setVisible(False)
        self._day_badge.setStyleSheet(
            "background:rgba(255,255,255,0.15); color:white; border-radius:10px; "
            "padding:5px 14px; font-size:12px; font-weight:600; border:1px solid rgba(255,255,255,0.25);"
        )
        hdr_lay.addWidget(self._day_badge)

        root.addWidget(header)

        # ── step indicator ────────────────────────────────────────────────────
        step_bar = QFrame()
        step_bar.setFixedHeight(44)
        step_bar.setStyleSheet(f"background:{C_PRIMARY_DARK};")
        step_lay = QHBoxLayout(step_bar)
        step_lay.setContentsMargins(28, 0, 28, 0)
        step_lay.setSpacing(0)

        self._step_labels: list[QLabel] = []
        for i, step in enumerate(STEPS):
            lbl = QLabel(step)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color:rgba(255,255,255,0.45); font-size:11px; font-weight:500; "
                f"letter-spacing:0.5px; padding:0 16px;"
            )
            self._step_labels.append(lbl)
            step_lay.addWidget(lbl, stretch=1)

            if i < len(STEPS) - 1:
                sep = QLabel("›")
                sep.setAlignment(Qt.AlignCenter)
                sep.setStyleSheet("color:rgba(255,255,255,0.25); font-size:14px;")
                step_lay.addWidget(sep)

        self._set_step(0)
        root.addWidget(step_bar)

        # ── stacked content area ──────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{C_BG};")

        self._s1 = Screen1(self.schedules, self.teacher_order)
        self._s2 = Screen2(self.schedules)
        self._s3 = Screen3()

        self._stack.addWidget(self._s1)   # index 0
        self._stack.addWidget(self._s2)   # index 1
        self._stack.addWidget(self._s3)   # index 2

        root.addWidget(self._stack, stretch=1)

        # ── wire signals ──────────────────────────────────────────────────────
        self._s1.proceed.connect(self._on_s1_proceed)
        self._s2.go_back.connect(self._go_to_s1)
        self._s2.proceed.connect(self._on_s2_proceed)
        self._s3.go_back.connect(self._go_to_s2)
        self._s3.start_over.connect(self._on_start_over)

    # ── step indicator ────────────────────────────────────────────────────────

    def _set_step(self, active: int):
        for i, lbl in enumerate(self._step_labels):
            if i < active:
                lbl.setStyleSheet(
                    f"color:rgba(255,255,255,0.65); font-size:11px; font-weight:500; "
                    f"letter-spacing:0.5px; padding:0 16px;"
                )
            elif i == active:
                lbl.setStyleSheet(
                    f"color:white; font-size:11px; font-weight:700; "
                    f"letter-spacing:0.5px; padding:0 16px; "
                    f"border-bottom:2px solid white;"
                )
            else:
                lbl.setStyleSheet(
                    f"color:rgba(255,255,255,0.35); font-size:11px; font-weight:400; "
                    f"letter-spacing:0.5px; padding:0 16px;"
                )

    # ── navigation ────────────────────────────────────────────────────────────

    def _on_s1_proceed(self, day: str, absent: list):
        self._session = logic.build_session(self.schedules, day, absent)
        self._day_badge.setText(f"  {day}  ")
        self._day_badge.setVisible(True)
        self._go_to_s2()

    def _go_to_s1(self):
        self._day_badge.setVisible(False)
        self._set_step(0)
        self._stack.setCurrentIndex(0)

    def _go_to_s2(self):
        self._set_step(1)
        self._s2.load_session(self._session)
        self._stack.setCurrentIndex(1)

    def _on_s2_proceed(self, session: dict):
        self._session = session
        self._set_step(2)
        self._s3.load_session(session)
        self._stack.setCurrentIndex(2)

    def _on_start_over(self):
        self._s1.reset()
        self._go_to_s1()
