# BR SSS Teacher Replacement - Web App

Mobile-friendly web version of the Teacher Replacement System.
Same workflow as the desktop PyQt app: select day, mark absent teachers, assign replacements, download PDF.

Designed like the school marklist site: static HTML/JS, works on phone and desktop, can be hosted on **GitHub Pages**.

## Folder layout

```
replaceweb/
  index.html
  css/app.css
  js/
    data-loader.js   # Excel parse + eligibility rules
    logic.js         # session / assignments
    pdf.js           # PDF download
    app.js           # UI screens
  data/
    latest-20-april.xlsx   # timetable (editable)
  README.md
```

## Run locally (required for Excel load)

Browsers block `fetch()` of local files under `file://`. Use a tiny server:

```bash
cd replaceweb
python3 -m http.server 8080
```

Then open: http://localhost:8080

On your phone (same Wi-Fi): http://YOUR-MAC-IP:8080

## Deploy to GitHub Pages

1. Create a GitHub repo (e.g. `replaceweb` or `brsss-replacement`).
2. Push this folder as the repo root (or put these files at the repo root).
3. GitHub -> **Settings** -> **Pages** -> Source: **Deploy from a branch** -> `main` / `/ (root)`.
4. Open the Pages URL on phone or computer.

Update the timetable by replacing `data/latest-20-april.xlsx` and pushing again.

## Business rules (same as desktop)

- Part-time MWF-only teachers only appear / cover on Mon, Wed, Fri
- Part-time Tue/Thu-only teachers only on Tue, Thu
- `OFF` in periods 1-7 = can still cover
- `OFF` in periods 8-9 = early leave, cannot cover
- One replacer cannot be double-booked for the same period

## Desktop app

The original PyQt desktop app remains in the parent folder (`../replacement_system/`). This web app is independent.
