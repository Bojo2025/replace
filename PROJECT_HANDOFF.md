# PROJECT_HANDOFF.md - BR SSS Teacher Replacement System

**Purpose of this document:** Give any new developer or Cursor agent full context to continue work without relying on prior chat history. Read this file first when opening the project on a new machine (especially Windows).

**School:** BR SSS (Belle Rose Secondary School)  
**App title:** BR SSS - Teacher Replacement System  
**Last updated:** May 2026 (handoff from macOS development)

---

## 1. What the application does

A **local desktop app** (Python + PyQt5) for daily teacher absence management:

1. Load the school timetable from an Excel file (`latest 20 april.xlsx`).
2. **Screen 1:** Pick the day (Mon-Fri) and mark which teachers are absent.
3. **Screen 2:** For each absent teacher, assign a replacement for every period they would have taught that day.
4. **Screen 3:** Review all assignments and **export a PDF** replacement sheet.

The original timetable comes from **aSc Timetables** (exported as PDF and converted to Excel). The app does **not** read the PDF at runtime - only the Excel file.

---

## 2. Repository layout

```
replace/                          <- project root (open this folder in Cursor)
  latest 20 april.xlsx            <- REQUIRED: timetable data (editable)
  latest 20 april.pdf             <- reference only; not used by the app at runtime
  replacement_system/             <- Python application
    main.py                       <- entry point
    data_loader.py                <- Excel parsing + eligibility rules
    replacement_logic.py          <- session state + replacement lookup
    pdf_generator.py              <- ReportLab PDF output
    ui/
      styles.py                   <- QSS stylesheet + colours
      main_window.py              <- header, steps, navigation
      screen1_select.py           <- day + absent teachers
      screen2_assign.py           <- period rows + replacement dropdowns
      screen3_review.py           <- summary table + PDF export
  build_windows/                  <- Windows EXE + installer build (run on Windows only)
    replace.spec                  <- PyInstaller config
    installer.iss                 <- Inno Setup script
    build.py                      <- one-command build
    BUILD_WINDOWS.md              <- detailed build steps
  run_replacement.sh              <- macOS/Linux launcher (uses .deps/)
  requirements.txt                <- runtime deps (Mac/dev)
  requirements-windows.txt        <- runtime + pyinstaller (Windows build)
  PROJECT_HANDOFF.md              <- this file
  Replacement_*.pdf             <- example outputs (optional)
```

**Do not copy `.deps/` to Windows** - it is a large local pip tree from Mac. Reinstall with `pip install -r requirements-windows.txt` instead.

**Git:** Repository may exist with little or no commits; prefer copying the whole `replace` folder or committing before transfer.

---

## 3. How to run the app

### macOS / Linux (development)

```bash
cd /path/to/replace
pip install openpyxl PyQt5 reportlab
# Optional: use local .deps like run_replacement.sh:
# PYTHONPATH=".deps" python3 replacement_system/main.py
python3 replacement_system/main.py
```

Or: `./run_replacement.sh` (sets `PYTHONPATH=.deps`).

### Windows (from source)

```cmd
cd C:\path\to\replace
pip install -r requirements-windows.txt
python replacement_system\main.py
```

**Timetable path:** `main.py` resolves `latest 20 april.xlsx` as:

- **From source:** parent folder of `replacement_system/` (project root).
- **Installed EXE (PyInstaller):** same folder as `BR_SSS_Replacement_System.exe` (see `sys.frozen` in `main.py`).

---

## 4. Timetable Excel format (critical)

### Current workbook shape

- **One worksheet** named `Page 1` containing **all ~78 teachers** (rows merged from former multi-page layout).
- Loader also supports: any sheets named `Page 1`, `Page 2`, ... **or**, if none match, **the first sheet only**.

### Row layout (1-indexed Excel rows)

| Row | Content |
|-----|---------|
| 1 | Metadata (`Source: latest 20 april.pdf`, etc.) |
| 2 | Blank |
| 3 | `BR SSS` |
| 4 | Day headers: Monday col B, Tuesday col O, Wednesday col AB, Thursday col AO, Friday col BB |
| 5 | Period labels: `1`, `2`, Morning Break, `3`..`9`, Lunch Break, etc. |
| 6+ | One row per teacher (name in column A) |

### Column grid per day (13 columns per day block)

Each day uses **13 columns**; only **9 are teaching periods** (break/register columns are skipped via `PERIOD_OFFSETS`):

| Period | Offset from day start column |
|--------|------------------------------|
| 1 | 0 |
| 2 | 1 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 7 |
| 7 | 8 |
| 8 | 11 |
| 9 | 12 |

`DAY_START_COLS` (1-based): Monday=2, Tuesday=15, Wednesday=28, Thursday=41, Friday=54.

### Cell values

- **Empty / None:** teacher is free that period (for timetable purposes).
- **`OFF`:** marked off / early leave (see business rules below).
- **Other text:** teaching assignment (e.g. `11 Art A 2.4`, `13 ST 13 ECO B 2.11`).

Names in column A may contain `\n` artefacts from PDF conversion; `_clean_name()` in `data_loader.py` normalizes them (e.g. `RAGNUT\nH` -> `RAGNUTH`).

### Source files

- `latest 20 april.pdf` - original aSc export (reference for staff; **not parsed by app**).
- `latest 20 april.xlsx` - **only file the app loads**.

### Important history - do NOT repeat these mistakes

1. **Do not rebuild Excel from PDF with a script** unless explicitly requested. A past attempt created **8 separate `Page *` sheets** and changed layout; user wanted **one sheet** and the **same grid** as before.
2. **Double/triple lessons in PDF** often appear as **one wide merged cell** in the PDF grid. If Excel only has text in the first period column, the app may under-count teaching periods. Fixing that belongs in **Excel data**, not by silently changing loader semantics without discussion.
3. **Do not bundle the Excel inside the EXE** if staff need to edit the timetable. Windows installer uses **Option B:** xlsx/pdf installed **next to** the executable (see `build_windows/`).

---

## 5. Business rules (implemented in code)

### 5.1 Part-time vs full-time teachers

Inferred from **which weekdays have any teaching** (`is_teaching` on any period 1-9):

| Pattern | `replacement_working_days()` returns | Example |
|---------|--------------------------------------|---------|
| Teaching only on Mon, Wed, Fri (subset of MWF, no Tue/Thu) | Mon, Wed, Fri | MOHANPE RSAD-BISS ONATH |
| Teaching only on Tue, Thu | Tue, Thu | APPIAH |
| Teaching on both MWF and Tue/Thu days, or mixed | All 5 days | Full-time |
| No teaching rows detected | All 5 days (safe default) | - |

**Where applied:**

- **Screen 1:** Absent-teacher checklist is **rebuilt when day changes** - only teachers who **work that weekday** appear (`screen1_select.py` + `replacement_working_days`).
- **Screen 2:** Replacement dropdown uses `get_free_teachers()` which also requires `day in replacement_working_days(...)`.

### 5.2 Who can appear in replacement dropdowns (Screen 2)

Implemented in `is_available_for_cover()` + `get_free_teachers()`:

| Condition | Eligible to cover? |
|-----------|-------------------|
| Currently **teaching** that period | No |
| **Empty** slot that period | Yes (if works that day) |
| **`OFF` in periods 1-7** | Yes (treated as free for cover) |
| **`OFF` in period 8 or 9** | **No** (early finish / gone home) |
| Not a working day for part-time pattern | No |
| Listed as absent today | No |
| Already assigned to cover same period for another absent teacher | No |

Dropdown list is **sorted alphabetically** (not Excel row order).

### 5.3 Absent teacher periods

`get_working_periods()` - periods where absent teacher has **non-empty, non-OFF** cell = must assign someone (or leave unassigned; PDF can still export with gaps).

---

## 6. Application architecture

```
main.py
  -> load_timetable(TIMETABLE) -> schedules, teacher_order
  -> MainWindow(schedules, teacher_order)
        -> Screen1(schedules, teacher_order)  -> proceed(day, absent[])
        -> Screen2(schedules)                 -> proceed(session)
        -> Screen3()                          -> go_back / start_over

replacement_logic.build_session(schedules, day, absent_teachers)
  -> session dict (see replacement_logic.py docstring)

replacement_logic.available_replacements(schedules, session, absent_teacher, period)
  -> get_free_teachers(...)
```

### Session object shape

```python
{
    "day": "Monday",
    "absent_teachers": ["TEACHER_A", ...],  # order from Screen 1
    "working_periods": {
        "TEACHER_A": [(1, "11 Art A 2.4"), (3, "12 ST/ 12 ECO A 2.4"), ...],
    },
    "assignments": {
        "TEACHER_A": {1: "REPLACER_NAME", 3: None, ...},  # period -> replacer or None
    },
}
```

---

## 7. UI behaviour notes

### Screen 1 - Select day and absent teachers

- Day buttons: Monday-Friday.
- Search filters visible checkboxes.
- Select All / Clear All affect **visible** teachers only.
- Changing day **clears and rebuilds** the teacher list for that day's working pattern.

### Screen 2 - Assign replacements

- One absent teacher at a time; progress bar.
- Each row: period badge, class info, **QComboBox** of eligible teachers, availability count pill.
- Back from Screen 3 -> Screen 2: **`load_session` resets to first absent teacher** (known behaviour).
- `_split_class_room()` in `screen2_assign.py` parses class vs room for display (regex for room codes like `A 2.7`, `Chem L 1`). Some labels still split imperfectly (e.g. `7 R` + `A 1.1`).

### Screen 3 - Review and PDF

- Table: absent, period, class, room, replaced by.
- **Generate PDF** opens save dialog; tries to open PDF after save (OS-specific).
- `session_complete()` exists but is **not** used to block PDF when unassigned rows remain.
- **Known bug:** `_refresh_view()` may accumulate extra spacers in chips row if `load_session` called repeatedly (minor layout leak).

---

## 8. Key modules reference

| Module | Responsibility |
|--------|----------------|
| `data_loader.py` | `load_timetable`, `is_teaching`, `is_free`, `is_off_cell`, `replacement_working_days`, `is_available_for_cover`, `get_free_teachers`, `get_working_periods` |
| `replacement_logic.py` | `build_session`, `available_replacements`, `assign_replacement`, `summary_rows`, `session_complete` |
| `pdf_generator.py` | ReportLab PDF; imports `_split_class_room` from UI layer |
| `ui/main_window.py` | Owns `schedules`, wires signals, step indicator |
| `ui/screen1_select.py` | Day selection + filtered absent list |
| `ui/screen2_assign.py` | Period rows + combos |
| `ui/screen3_review.py` | Review table + PDF button |

---

## 9. Dependencies

**Runtime (`requirements.txt`):**

- openpyxl >= 3.1.0
- PyQt5 >= 5.15.0
- reportlab >= 4.0.0

**Windows build (`requirements-windows.txt`):** above + pdfplumber >= 0.11.0 (only needed if rebuilding Excel from PDF - **not used at app runtime**) + pyinstaller >= 6.0.0

---

## 10. Windows installer build (must run on Windows)

PyInstaller on Mac produces macOS binaries, **not** Windows `.exe`. Build on the Windows laptop:

1. Install **Python 3.11+**, **Inno Setup 6** (https://jrsoftware.org/isdl.php).
2. Copy entire `replace` folder to Windows.
3. Run:

```cmd
cd C:\path\to\replace
pip install -r requirements-windows.txt
cd build_windows
python build.py
```

**Outputs** (`build_windows\dist\`):

- `BR_SSS_Replacement_System\BR_SSS_Replacement_System.exe` - application folder (`onefile=False` in `replace.spec`; ship the whole folder if not using the installer).
- `BR_SSS_Replacement_Setup.exe` - installer (if Inno Setup found).

**Installer layout (Option B - editable timetable):**

- EXE + support files in `C:\Program Files\BR SSS Teacher Replacement System\`
- `latest 20 april.xlsx` and `latest 20 april.pdf` copied **beside** the EXE (not inside the binary).
- Staff edit xlsx in Excel; **restart app** to reload.

See `build_windows/BUILD_WINDOWS.md` for troubleshooting (antivirus false positives, icons, etc.).

**Removed / do not restore without discussion:** `replacement_system/pdf_timetable_rebuild.py` - a PDF-to-Excel rebuild script that was deleted after it split the workbook into 8 sheets and broke the expected layout.

---

## 10b. Transfer checklist (Mac to Windows laptop)

| Copy to Windows | Do NOT copy (reinstall / rebuild on Windows) |
|-----------------|-----------------------------------------------|
| `replacement_system/` | `.deps/` |
| `build_windows/` (sources only) | `build_windows/build/` |
| `latest 20 april.xlsx` (required) | `build_windows/dist/` |
| `latest 20 april.pdf` | `__pycache__/`, `*.pyc` |
| `requirements*.txt`, `run_replacement.sh` | `.git/` (optional) |
| `PROJECT_HANDOFF.md` | |

**Must exist at project root:** `latest 20 april.xlsx` (app shows error and exits if missing).

**On Windows in Cursor:** Open the `replace` folder -> New Agent chat -> say: *Read PROJECT_HANDOFF.md in the project root, then [your task].*

---

## 11. Verification examples (sanity checks)

Run from project root with `replacement_system` on `PYTHONPATH` or from inside `replacement_system/`:

```python
import sys
sys.path.insert(0, "replacement_system")
from data_loader import load_timetable, get_free_teachers, replacement_working_days

sched, order = load_timetable("latest 20 april.xlsx")

# Part-time
appiah = next(t for t in order if t.upper() == "APPIAH")
mohan = next(t for t in order if "MOHANPE" in t.upper())
assert replacement_working_days(sched, appiah) == frozenset({"Tuesday", "Thursday"})
assert replacement_working_days(sched, mohan) == frozenset({"Monday", "Wednesday", "Friday"})

# Appiah never in Monday pool for any period
for p in range(1, 10):
    assert appiah not in get_free_teachers(sched, "Monday", p)
```

---

## 12. Known issues / future improvements (not yet done)

| Item | Notes |
|------|--------|
| Screen 3 chips row | `addStretch()` on each refresh may stack spacers |
| Screen 2 back from review | Always returns to **first** absent teacher |
| PDF with unassigned | Allowed; badge shows unassigned count |
| `session_complete()` | Unused in UI |
| Class/room split regex | Some timetable strings still display merged (e.g. `7 RA 1.1` vs `7 R` + `A 1.1`) |
| `pdf_generator` -> UI import | `_split_class_room` lives in `screen2_assign.py`; consider moving to shared util |
| `.gitignore` | Not added; exclude `.deps/`, `__pycache__/`, `build_windows/build/`, `build_windows/dist/` before first commit |

---

## 13. Instructions for the Cursor agent on Windows

When the user opens this project in Cursor on Windows:

1. **Read this file** and `build_windows/BUILD_WINDOWS.md` if building an installer.
2. **Do not** change Excel workbook structure (single `Page 1` sheet, row/column layout) without explicit user approval.
3. **Preserve** part-time and P8/P9 OFF rules in `data_loader.py` unless the user changes policy.
4. **Test** with `python replacement_system\main.py` from project root after edits.
5. For UI changes, match existing patterns in `ui/styles.py` (blue header `#1565C0`, card layout).
6. User may want: installer build, UI fixes, better class/room parsing, or timetable updates - ask if unclear.

**First message suggestion for user to paste:**

> Read PROJECT_HANDOFF.md in the project root, then help me with: [their task].

---

## 14. Contact / context

- Timetable file name is fixed in code as `latest 20 april.xlsx` (change `TIMETABLE` in `main.py` if the school provides a new file name).
- Generated PDFs default to names like `Replacement_{Day}_{YYYY-MM-DD}.pdf` from Screen 3 save dialog.

---

*End of handoff document.*

---

## Web app (GitHub Pages)

The mobile web version lives in **`docs/`** (required folder name for GitHub Pages).

- Handoff: `docs/PROJECT_HANDOFF.md`
- Site: https://bojo2025.github.io/replace/
- Pages setting: branch `main`, folder `/docs`
