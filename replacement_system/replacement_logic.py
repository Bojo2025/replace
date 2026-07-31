"""
Session state and replacement logic for the teacher replacement workflow.

Session structure
-----------------
{
    "day": "Monday",
    "absent_teachers": ["TEACHER_A", "TEACHER_B", ...],   # in selection order

    # assignments[absent_teacher][period] = replacing_teacher_name | None
    "assignments": {
        "TEACHER_A": {1: None, 3: "TEACHER_X", ...},
        ...
    },

    # working_periods[absent_teacher] = [(period, class_label), ...]
    # only periods where the teacher IS teaching (not free/OFF)
    "working_periods": {
        "TEACHER_A": [(1, "13 ECO A 2.7"), (3, "12 ST A 2.5"), ...],
        ...
    },
}
"""

from __future__ import annotations
from collections import defaultdict
from data_loader import get_working_periods, get_free_teachers, DAYS, PERIODS


def build_session(schedules, day: str, absent_teachers: list[str]) -> dict:
    """Initialise a fresh session for the given day and absent-teacher list."""
    session: dict = {
        "day": day,
        "absent_teachers": list(absent_teachers),
        "assignments": {},
        "working_periods": {},
    }

    for teacher in absent_teachers:
        wps = get_working_periods(schedules, teacher, day)
        session["working_periods"][teacher] = wps
        session["assignments"][teacher] = {p: None for p, _ in wps}

    return session


def _committed_for_period(session: dict, period: int,
                           current_absent: str | None = None) -> set[str]:
    """
    Return the set of teachers already assigned to cover `period`
    for ANY absent teacher *other* than `current_absent`.
    This prevents double-booking.
    """
    committed: set[str] = set()
    for absent_t, period_map in session["assignments"].items():
        if absent_t == current_absent:
            continue
        replacer = period_map.get(period)
        if replacer:
            committed.add(replacer)
    return committed


def available_replacements(schedules, session: dict,
                            absent_teacher: str, period: int) -> list[str]:
    """
    List of teachers who can replace `absent_teacher` at `period`.

    Excludes:
      - All absent teachers (they can't cover their own period either)
      - Any teacher already assigned to cover this period for another absent teacher
      - Teachers who don't work that weekday (part-time MWF vs Tue/Thu patterns)
      - Teachers with OFF in period 8 or 9 on that day (early leave — not for cover)
    """
    exclude = set(session["absent_teachers"])
    exclude |= _committed_for_period(session, period, current_absent=absent_teacher)

    return get_free_teachers(schedules, session["day"], period, exclude=exclude)


def assign_replacement(session: dict, absent_teacher: str,
                       period: int, replacing_teacher: str | None) -> None:
    """Record (or clear) a replacement assignment."""
    if absent_teacher in session["assignments"]:
        session["assignments"][absent_teacher][period] = replacing_teacher


def get_assignment(session: dict, absent_teacher: str, period: int) -> str | None:
    return session["assignments"].get(absent_teacher, {}).get(period)


def summary_rows(session: dict) -> list[dict]:
    """
    Flatten the session into a list of row dicts for display / PDF.

    Each row:
    {
        "absent":   str,
        "period":   int,
        "class":    str,
        "replacer": str | None,   # None = no replacement assigned
    }
    """
    rows = []
    for teacher in session["absent_teachers"]:
        for period, class_label in session["working_periods"].get(teacher, []):
            replacer = session["assignments"].get(teacher, {}).get(period)
            rows.append({
                "absent":   teacher,
                "period":   period,
                "class":    class_label or "",
                "replacer": replacer,
            })
    return rows


def session_complete(session: dict) -> bool:
    """True if every working period for every absent teacher has been assigned."""
    for teacher in session["absent_teachers"]:
        for period, _ in session["working_periods"].get(teacher, []):
            if not session["assignments"].get(teacher, {}).get(period):
                return False
    return True
