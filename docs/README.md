# BR SSS Teacher Replacement — Web App

Mobile-friendly web version of the Teacher Replacement System.
Same workflow: select day, mark absent teachers, assign replacements, download PDF.

This folder (`docs/`) is what **GitHub Pages** publishes.

## Live site

After Pages is enabled (`main` → `/docs`):

https://bojo2025.github.io/replace/

## Run locally

```bash
cd docs
python3 -m http.server 8080
```

Open: http://localhost:8080

## Layout

```
docs/
  index.html
  css/app.css
  js/          data-loader.js, logic.js, pdf.js, app.js
  data/latest-20-april.xlsx
  PROJECT_HANDOFF.md
  .nojekyll
```

## Business rules

Same as desktop: part-time MWF / Tue-Thu, OFF in P8-P9 cannot cover, no double-booking.

See PROJECT_HANDOFF.md for full details.
