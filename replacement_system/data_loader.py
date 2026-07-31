"""
Parse the teacher timetable from the Excel file generated from the aSc PDF.

Excel structure (from analysis):
  Row 1 : metadata  ("Source: ...")
  Row 2 : blank
  Row 3 : "BR SSS"
  Row 4 : day-name headers   (Monday at col B=2, Tuesday at col O=15, ...)
  Row 5 : period labels      (1, 2, Morning Break, 3, 4, 5, Lunch Break, 6, 7, ...)
  Row 6+: one row per teacher

Worksheets: if any sheet name starts with "Page ", only those sheets are read
(in order). Otherwise the first worksheet is read as a single timetable sheet.

Each day block is 13 columns wide:
  offset 0  → period 1
  offset 1  → period 2
  offset 2  → Morning Break  (skip)
  offset 3  → period 3
  offset 4  → period 4
  offset 5  → period 5
  offset 6  → Lunch Break    (skip)
  offset 7  → period 6
  offset 8  → period 7
  offset 9  → Afternoon Break (skip)
  offset 10 → Afternoon Register (skip)
  offset 11 → period 8
  offset 12 → period 9
"""

import re
import openpyxl

# 1-indexed start columns for each day
DAY_START_COLS = {
    "Monday":    2,
    "Tuesday":   15,
    "Wednesday": 28,
    "Thursday":  41,
    "Friday":    54,
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS = list(range(1, 10))   # 1 … 9

# Part-time patterns (replacement pool: only these weekdays)
_MWF_DAYS = frozenset({"Monday", "Wednesday", "Friday"})
_TUTH_DAYS = frozenset({"Tuesday", "Thursday"})
_ALL_DAYS = frozenset(DAYS)

# Offset from the day-start column (0-indexed) for each teaching period
PERIOD_OFFSETS = {1: 0, 2: 1, 3: 3, 4: 4, 5: 5, 6: 7, 7: 8, 8: 11, 9: 12}

ROW_DATA_START = 6   # first teacher-data row (1-indexed)

# ── name cleaning ────────────────────────────────────────────────────────────

def _clean_name(raw) -> str | None:
    """
    Turn a raw cell value (may contain \\n wrapping artefacts) into a clean
    display name.  Uses context to decide whether \\n means continuation or
    a word boundary.
    """
    if not raw:
        return None
    parts = str(raw).split("\n")
    result = parts[0]
    for part in parts[1:]:
        if not part:
            continue
        prev_end  = result[-1] if result else ""
        next_start = part[0]
        # lowercase continuation (e.g. "Rajcooma" + "r")
        if next_start.islower():
            result += part
        # after a hyphen (e.g. "DOWLUT-" + "POORUN")
        elif prev_end == "-":
            result += part
        # very short ALL-CAPS fragment = word-ending (e.g. "SEELOC" + "HUN")
        elif part.isupper() and len(part) <= 4:
            result += part
        else:
            result += " " + part
    return re.sub(r"\s+", " ", result).strip() or None


# ── cell-value cleaning ───────────────────────────────────────────────────────

def _clean_cell(raw) -> str | None:
    """
    Normalise a schedule cell value.
    Collapses whitespace/newlines and fixes split single-letter words
    (e.g. "E\\nC\\nO" → "ECO", "S\\nT" → "ST").
    """
    if raw is None:
        return None
    text = " ".join(str(raw).split())
    if not text:
        return None
    # Fix 3-letter splits: "E C O" → "ECO"
    text = re.sub(r"(?<!\w)([A-Z]) ([A-Z]) ([A-Z])(?!\w)", r"\1\2\3", text)
    # Fix 2-letter splits: "S T" → "ST"
    text = re.sub(r"(?<!\w)([A-Z]) ([A-Z])(?!\w)", r"\1\2", text)
    return text


# ── public helpers ────────────────────────────────────────────────────────────

def is_free(cell_val: str | None) -> bool:
    """True when the slot is free (None, empty, or starts with OFF)."""
    if not cell_val:
        return True
    return cell_val.strip().upper().startswith("OFF")


def is_teaching(cell_val: str | None) -> bool:
    return bool(cell_val) and not is_free(cell_val)


def is_off_cell(cell_val: str | None) -> bool:
    """True when the cell is an explicit OFF / early-leave marker (not empty)."""
    if not cell_val:
        return False
    return cell_val.strip().upper().startswith("OFF")


def _teaching_days(schedules: dict, teacher: str) -> set[str]:
    """Weekdays where the teacher has at least one teaching period."""
    days_map = schedules.get(teacher, {})
    out: set[str] = set()
    for d in DAYS:
        for p in PERIODS:
            if is_teaching(days_map.get(d, {}).get(p)):
                out.add(d)
                break
    return out


def replacement_working_days(schedules: dict, teacher: str) -> frozenset[str]:
    """
    Weekdays on which this teacher may be offered as a replacement.

    Full-time (or mixed patterns): all five days.
    Part-time Mon/Wed/Fri only: those three days (inferred from teaching days).
    Part-time Tue/Thu only: those two days.
    If there is no teaching data for the teacher, all five days (safe default).
    """
    td = _teaching_days(schedules, teacher)
    if not td:
        return _ALL_DAYS
    if td <= _MWF_DAYS and td.isdisjoint(_TUTH_DAYS):
        return _MWF_DAYS
    if td <= _TUTH_DAYS and td.isdisjoint(_MWF_DAYS):
        return _TUTH_DAYS
    return _ALL_DAYS


def is_available_for_cover(schedules: dict, teacher: str, day: str, period: int) -> bool:
    """
    True if ``teacher`` can substitute in ``period`` on ``day``.

    Teaching blocks coverage.  For periods 8–9, OFF means early finish — not
    available to cover.  For periods 1–7, OFF still counts as available (free slot).
    Empty slot is available.
    """
    cell = schedules.get(teacher, {}).get(day, {}).get(period)
    if is_teaching(cell):
        return False
    if period in (8, 9) and is_off_cell(cell):
        return False
    return True


# ── main loader ───────────────────────────────────────────────────────────────

_SKIP_KEYWORDS = {
    "SOURCE", "BR SSS", "TIMETABLE GENERATED", "MONDAY", "TUESDAY",
    "WEDNESDAY", "THURSDAY", "FRIDAY", "PERIOD", "MORNING BREAK",
    "LUNCH BREAK", "AFTERNOON", "SUMMARY", "PAGE", "GENERATED",
}


def load_timetable(xlsx_path: str):
    """
    Parse the Excel timetable file.

    Returns
    -------
    schedules : dict[teacher_name, dict[day, dict[period, str|None]]]
        schedules[teacher][day][period] is the cleaned cell text, or None
        when the teacher is free.
    teacher_order : list[str]
        Teacher names in the order they appear in the file.
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)

    schedules: dict = {}
    teacher_order: list[str] = []
    seen: set[str] = set()

    page_sheets = [ws for ws in wb.worksheets if ws.title.startswith("Page ")]
    if not page_sheets:
        page_sheets = [wb.worksheets[0]]

    for ws in page_sheets:
        for row in ws.iter_rows(min_row=ROW_DATA_START, values_only=True):
            if not any(row):
                continue

            raw_name = row[0]
            name = _clean_name(raw_name)
            if not name:
                continue

            # Skip header / metadata rows
            name_upper = name.upper()
            if any(kw in name_upper for kw in _SKIP_KEYWORDS):
                continue
            if name_upper.replace(" ", "").isdigit():
                continue
            # Skip period/break labels that leak into column A
            if name_upper in {"1", "2", "3", "4", "5", "6", "7", "8", "9",
                               "MORNING BREAK", "LUNCH BREAK", "AFTERNOON BREAK",
                               "AFTERNOON REGISTER"}:
                continue

            # Deduplicate names
            base = name
            suffix = 2
            while name in seen:
                name = f"{base} ({suffix})"
                suffix += 1
            seen.add(name)
            teacher_order.append(name)

            schedules[name] = {}
            for day, start_col in DAY_START_COLS.items():
                schedules[name][day] = {}
                for period, offset in PERIOD_OFFSETS.items():
                    col_idx = (start_col - 1) + offset   # 0-indexed
                    val = row[col_idx] if col_idx < len(row) else None
                    schedules[name][day][period] = _clean_cell(val)

    return schedules, teacher_order


# ── query functions ───────────────────────────────────────────────────────────

def get_working_periods(schedules, teacher: str, day: str) -> list[tuple[int, str]]:
    """Return [(period, class_label), …] for periods the teacher is teaching."""
    result = []
    for p in PERIODS:
        cell = schedules.get(teacher, {}).get(day, {}).get(p)
        if is_teaching(cell):
            result.append((p, cell))
    return result


def get_free_teachers(schedules, day: str, period: int,
                      exclude: set | None = None) -> list[str]:
    """
    Return sorted teachers eligible to cover a class at (day, period).

    Excludes ``exclude``.  Applies part-time working-day rules (MWF vs Tue/Thu),
    slot availability, and for periods 8–9 treats OFF as unavailable (early leave).
    """
    exclude = exclude or set()
    return sorted(
        t for t in schedules
        if t not in exclude
        and day in replacement_working_days(schedules, t)
        and is_available_for_cover(schedules, t, day, period)
    )
