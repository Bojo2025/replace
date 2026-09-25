# PROJECT_HANDOFF.md - BR SSS Teacher Replacement (Web)

**Purpose:** Full context for continuing this project on another Mac (e.g. M5) or any machine / Cursor agent. Read this first; do not rely on prior chat history.

**School:** BR SSS (Belle Rose Secondary School / B. Ramlallah SSS)  
**App:** Teacher Replacement System - **web version**  
**Created from:** Desktop PyQt app in parent folder `../replacement_system/`  
**UI style:** Same idea as the school **online marklist** (`results` / `markzv3`) - static HTML/JS, mobile-first, GitHub Pages friendly  
**Last updated:** September 2026

---

## 1. What this app is

A **browser web app** (no Python server required) for daily teacher absences:

1. Load timetable from Excel (`data/latest-20-april.xlsx`).
2. **Screen 1:** Select day (Mon-Fri) + mark absent teachers.
3. **Screen 2:** For each absent teacher, assign a replacement per teaching period.
4. **Screen 3:** Review + **Download PDF**.

Works on **phone and desktop**. Can be hosted on **GitHub Pages** like the marklist.

**Not the same as:** the PyQt desktop app in `../replacement_system/` (still exists; Windows installer lives in `../build_windows/`). This web app is independent but copies the same business rules.

---

## 2. Folder layout (this project)

Open **`replaceweb/`** as the Cursor workspace root when continuing web work.

```
replaceweb/
  index.html              Entry page (screens + CDN libs)
  css/app.css             Mobile-first styles (marklist-like colours)
  js/
    data-loader.js        Excel parse + eligibility (port of data_loader.py)
    logic.js              Session / assignments (port of replacement_logic.py)
    pdf.js                PDF via jsPDF + autoTable
    app.js                UI: screens, navigation, bottom bar
  data/
    latest-20-april.xlsx  REQUIRED timetable (78 teachers, sheet "Page 1")
  README.md               Short user/run notes
  PROJECT_HANDOFF.md      This file
  .gitignore
```

**Sibling (parent repo, optional):**

```
replace/                          Parent folder on the Mid-2015 Mac
  replacement_system/             Desktop PyQt app
  PROJECT_HANDOFF.md              Desktop handoff (Windows EXE, etc.)
  latest 20 april.xlsx            Original timetable filename
  replaceweb/                     <-- THIS web project
```

When copying to the M5: copy the whole **`replaceweb`** folder (or the whole `replace` parent if you want both apps).

---

## 3. How to run (M5 / any Mac)

Browsers **cannot** load the Excel via `file://` (fetch is blocked). Always use a local server:

```bash
cd /path/to/replaceweb
python3 -m http.server 8080
```

Open: http://localhost:8080

Phone on same Wi-Fi: http://YOUR-MAC-IP:8080

No npm/Node required for basic use. Libraries load from CDN:

- SheetJS (xlsx) - Excel parse
- jsPDF + jspdf-autotable - PDF export

---

## 4. Deploy to GitHub Pages

1. Create a GitHub repo (e.g. `brsss-replacement` or `replaceweb`).
2. Push **contents of `replaceweb/`** as the repo root (so `index.html` is at root).
3. GitHub -> Settings -> Pages -> Deploy from branch `main` / `/ (root)`.
4. Use the Pages URL on phone or PC.

Update timetable: replace `data/latest-20-april.xlsx`, commit, push. Refresh the site.

CDN scripts need network access on first load.

---

## 5. Timetable Excel format (critical - same as desktop)

### Workbook

- File used by web app: `data/latest-20-april.xlsx`
- Usually **one sheet** named `Page 1` with all ~**78 teachers**
- Loader also accepts multiple sheets named `Page 1`, `Page 2`, ... or falls back to the **first sheet**

### Rows (1-indexed Excel)

| Row | Content |
|-----|---------|
| 1-5 | Headers / metadata |
| 6+  | One teacher per row; name in column A |

### Day start columns (1-based)

Monday=2, Tuesday=15, Wednesday=28, Thursday=41, Friday=54  
Each day block is **13 columns**; teaching periods use offsets:

| Period | Offset |
|--------|--------|
| 1 | 0 |
| 2 | 1 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 7 |
| 7 | 8 |
| 8 | 11 |
| 9 | 12 |

(Break / register columns are skipped.)

### Cell values

- Empty = free
- Text starting with `OFF` = off / early leave
- Other text = teaching (e.g. `11 Art A 2.4`)

**Do not** rebuild the Excel from PDF into 8 separate sheets unless the user explicitly asks - that broke layout before (see parent desktop handoff).

---

## 6. Business rules (must preserve)

Implemented in `js/data-loader.js` + `js/logic.js`:

### Part-time working days

Inferred from which weekdays the teacher actually teaches:

| Pattern | Can be absent / cover on |
|---------|--------------------------|
| Teaching only Mon/Wed/Fri | Mon, Wed, Fri only |
| Teaching only Tue/Thu | Tue, Thu only |
| Mixed / full-time | All 5 days |
| No teaching data | All 5 days (safe default) |

Examples: **APPIAH** = Tue/Thu; **MOHANPE...** = Mon/Wed/Fri.

Screen 1 only lists teachers who work that day. Screen 2 dropdowns use the same rule.

### Who can cover a period

| Condition | Eligible? |
|-----------|-----------|
| Teaching that period | No |
| Empty slot | Yes |
| OFF in periods 1-7 | Yes |
| OFF in period 8 or 9 | **No** (gone home) |
| Not a working day for them | No |
| Listed absent today | No |
| Already assigned same period for another absent teacher | No |

Dropdowns sorted **alphabetically**.

### Absent periods

Only periods where the absent teacher is **teaching** (non-empty, non-OFF) need a replacement. PDF can still export with unassigned gaps.

---

## 7. Architecture

```
index.html
  loads CDN: SheetJS, jsPDF, autoTable
  loads js/data-loader.js -> window.DataLoader
  loads js/logic.js       -> window.ReplacementLogic
  loads js/pdf.js         -> window.PdfExport
  loads js/app.js         -> boots UI

Boot:
  fetch(data/latest-20-april.xlsx)
  -> DataLoader.loadTimetable
  -> schedules + teacherOrder
  -> Screen 1

Session object (same shape as desktop):
{
  day: "Monday",
  absent_teachers: ["A", "B"],
  working_periods: { "A": [[1, "11 Art A 2.4"], ...] },
  assignments: { "A": { 1: "REPLACER" or null, ... } }
}
```

### UI notes

- Sticky top bar + step pills + fixed bottom action bar (mobile-friendly)
- Colours match marklist-ish theme: `--primary #1a1a2e`, `--accent #4f8ef7`
- Start over clears session
- Back from review returns to assign at **first** absent teacher (same quirk as desktop)

---

## 8. Key files to edit

| Change | Edit |
|--------|------|
| UI / screens / buttons | `js/app.js`, `css/app.css`, `index.html` |
| Excel layout / OFF / part-time rules | `js/data-loader.js` |
| Session / double-booking | `js/logic.js` |
| PDF look / columns | `js/pdf.js` |
| Timetable data | `data/latest-20-april.xlsx` |
| Timetable path/filename | `TIMETABLE_URL` in `js/app.js` |

---

## 9. Sanity checks after logic changes

In browser DevTools console (after app loaded):

```javascript
const appiah = teacherOrder.find(t => t.toUpperCase() === "APPIAH");
// Or after exposing schedules globally - currently schedules is private in app.js.
// Prefer temporary console.log in boot, or:
```

Better: temporary test in console by loading via DataLoader:

```javascript
DataLoader.loadTimetable("data/latest-20-april.xlsx").then(({schedules, teacherOrder}) => {
  const appiah = teacherOrder.find(t => t.toUpperCase() === "APPIAH");
  console.log([...DataLoader.replacementWorkingDays(schedules, appiah)]);
  // expect Tuesday, Thursday
  console.log(teacherOrder.length); // ~78
});
```

Desktop Python check (from parent folder, if `.deps` present):

```bash
cd ..
PYTHONPATH=".deps:replacement_system" python3 -c "
from data_loader import load_timetable, replacement_working_days
s,o=load_timetable('replaceweb/data/latest-20-april.xlsx')
print(len(o), sorted(replacement_working_days(s, next(t for t in o if t.upper()=='APPIAH'))))
"
```

---

## 10. Known gaps / possible next work

| Item | Notes |
|------|--------|
| No login | Marklist has Google login; this app is open to anyone with the URL |
| No shared live state | Each browser has its own session; not multi-user realtime |
| Timetable update | Manual replace of xlsx + redeploy (or add upload UI later) |
| CDN dependency | Offline school network may block SheetJS/jsPDF CDNs - consider vendoring libs under `vendor/` |
| Class/room split | Same imperfect regex as desktop (`DataLoader.splitClassRoom`) |
| Desktop vs web drift | If you change rules, update **both** Python and JS, or treat web as the only product going forward |
| Git remote | `replaceweb` may have local `.git` without `origin` yet - add remote on M5 when pushing to GitHub |

---

## 11. Transfer checklist (Mid-2015 Mac -> M5)

Copy **`replaceweb/`** entire folder (USB exFAT is fine).

**Ready-made zip (on the Mid-2015 Mac):**

`replaceweb/replaceweb-for-M5.zip`

Contains: `index.html`, `css/`, `js/`, `data/latest-20-april.xlsx`, `PROJECT_HANDOFF.md`, `README.md`.  
Copy that zip to the pen drive, unzip on the M5, open the `replaceweb` folder in Cursor.

| Include | Optional / skip |
|---------|-----------------|
| All of `replaceweb/` (or the zip above) | Parent `.deps/` (desktop only) |
| Especially `data/latest-20-april.xlsx` | `../build_windows/` unless you still need Windows EXE |
| This `PROJECT_HANDOFF.md` | Large PDF samples |
| Skip `replaceweb-for-M5.zip` after unzipping on M5 | |

On M5:

1. Open `replaceweb` in Cursor.
2. New Agent: *Read PROJECT_HANDOFF.md, then help me with: ...*
3. Run `python3 -m http.server 8080` and test at localhost:8080.
4. When ready, push to GitHub Pages (`gh auth login` may be needed if token expired).

---

## 12. Instructions for the Cursor agent on M5

1. Read **this file** first.
2. Prefer editing the **web** app under `replaceweb/` unless the user asks about the desktop PyQt app.
3. **Do not** change Excel sheet structure without user approval.
4. **Preserve** part-time and P8/P9 OFF rules unless policy changes.
5. Keep UI mobile-first (large tap targets, bottom bar, marklist-like look).
6. After changes, verify with local `python3 -m http.server` - not by double-clicking `index.html`.
7. Write new docs/code as **UTF-8 / ASCII-safe** punctuation when possible (avoid smart dashes that break encoding).

**Suggested first message:**

> Read PROJECT_HANDOFF.md in replaceweb, then help me with: [task].

---

## 13. Relationship to desktop handoff

Parent file: `../PROJECT_HANDOFF.md` (desktop PyQt + Windows installer).

| Topic | Desktop | Web (this repo) |
|-------|---------|-----------------|
| Runtime | Python + PyQt5 | Browser only |
| Excel | `latest 20 april.xlsx` at project root | `data/latest-20-april.xlsx` |
| PDF | ReportLab | jsPDF |
| Hosting | Local EXE / installer | GitHub Pages |
| Phone | No | Yes |

---

*End of web handoff document.*
