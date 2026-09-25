# PROJECT_HANDOFF.md - BR SSS Teacher Replacement (Web)

**COPY THIS FOLDER ONLY.** You do **not** need the big parent `replace` folder or any desktop/PyQt software.

**What to put on the USB / M5:** the entire **`docs`** folder (this folder). That is the full web app.

**School:** BR SSS (Belle Rose Secondary School)  
**App:** Teacher Replacement System - web version (phone + laptop)  
**Live site:** https://bojo2025.github.io/replace/  
**Repo:** https://github.com/Bojo2025/replace  
**Last updated:** September 2026

---

## Start here on the M5

1. Copy the **`docs`** folder from the USB (or clone the GitHub repo and open `docs`).
2. Open **`docs`** in Cursor (File → Open Folder → select `docs`).
3. In Terminal:

```bash
cd /path/to/docs
python3 -m http.server 8080
```

4. Browser: http://localhost:8080  
5. New Cursor Agent chat: *Read PROJECT_HANDOFF.md, then help me with: …*

**Do not** double-click `index.html` — the Excel timetable will not load. Always use the local server (or the live GitHub Pages URL).

---

## 1. What this app does

Browser app (HTML/JS, no install):

1. Loads `data/latest-20-april.xlsx`
2. Pick day + absent teachers
3. Assign replacements period by period
4. Download PDF sheet

Same idea as the school online marklist: static site, works on phone, GitHub Pages.

---

## 2. Everything in this folder (complete list)

```
docs/                         <- COPY THIS WHOLE FOLDER
  index.html                  App UI
  css/app.css                 Styles
  js/
    data-loader.js            Excel + eligibility rules
    logic.js                  Session / assignments
    pdf.js                    PDF download
    app.js                    Screens / buttons
  data/
    latest-20-april.xlsx      Timetable (required, ~78 teachers)
  PROJECT_HANDOFF.md          This file
  README.md                   Short run notes
  .nojekyll                   Needed for GitHub Pages
  .gitignore
```

If any of these are missing, the app is incomplete. The timetable Excel **must** be present.

Libraries (SheetJS, jsPDF) load from the internet (CDN) when you open the site.

---

## 3. GitHub Pages

Already set up to publish **this** `docs/` folder.

- Settings → Pages → branch **`main`**, folder **`/docs`**
- URL: https://bojo2025.github.io/replace/

Edit files here → commit → push from the parent git repo (or ask the agent on M5 after cloning).

---

## 4. Timetable Excel format

- File: `data/latest-20-april.xlsx`
- Sheet: usually `Page 1`, all teachers from row 6
- Day blocks: Mon col 2, Tue 15, Wed 28, Thu 41, Fri 54
- Periods 1-9 use offsets 0,1,3,4,5,7,8,11,12 within each day block
- Empty = free; `OFF` = off; other text = teaching

Do not rebuild into 8 separate sheets unless asked.

---

## 5. Business rules (keep these)

**Part-time:**
- Teaching only Mon/Wed/Fri → only those days (absent list + cover pool)
- Teaching only Tue/Thu → only those days
- Otherwise → all 5 days
- Examples: APPIAH = Tue/Thu; MOHANPE… = Mon/Wed/Fri

**Cover eligibility:**
- Teaching that period → no
- Empty → yes
- OFF in periods 1-7 → yes
- OFF in periods 8-9 → **no**
- Absent today → no
- Already covering same period elsewhere → no

---

## 6. Architecture

```
index.html
  -> CDN: SheetJS, jsPDF, autoTable
  -> js/data-loader.js  (DataLoader)
  -> js/logic.js        (ReplacementLogic)
  -> js/pdf.js          (PdfExport)
  -> js/app.js          (UI)

Session:
{
  day, absent_teachers,
  working_periods: { teacher: [[period, classLabel], ...] },
  assignments: { teacher: { period: replacerOrNull } }
}
```

---

## 7. What to edit

| Change | File |
|--------|------|
| UI / flow | `js/app.js`, `css/app.css`, `index.html` |
| Rules / Excel layout | `js/data-loader.js` |
| Assignments / double-book | `js/logic.js` |
| PDF | `js/pdf.js` |
| Timetable data | `data/latest-20-april.xlsx` |

---

## 8. For the Cursor agent on M5

1. Read **this file** first.
2. Workspace root should be this **`docs`** folder.
3. Do not require the parent desktop app.
4. Preserve part-time and P8/P9 OFF rules.
5. Test with `python3 -m http.server 8080`, not `file://`.
6. Keep mobile-friendly UI.

---

## 9. You do NOT need

- The huge parent `replace` folder
- `replacement_system/` (old desktop PyQt app)
- `.deps/`, `build_windows/`, `replaceweb/` (old name; site is here in `docs/`)

**Only this `docs` folder.**

---

*End of handoff.*
