/**
 * Excel timetable loader - port of replacement_system/data_loader.py
 * Parses SheetJS workbook rows into schedules + teacher_order.
 */
(function (global) {
  "use strict";

  const DAY_START_COLS = {
    Monday: 2,
    Tuesday: 15,
    Wednesday: 28,
    Thursday: 41,
    Friday: 54,
  };

  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9];
  const PERIOD_OFFSETS = { 1: 0, 2: 1, 3: 3, 4: 4, 5: 5, 6: 7, 7: 8, 8: 11, 9: 12 };
  const ROW_DATA_START = 6; // 1-indexed Excel row

  const MWF_DAYS = new Set(["Monday", "Wednesday", "Friday"]);
  const TUTH_DAYS = new Set(["Tuesday", "Thursday"]);
  const ALL_DAYS = new Set(DAYS);

  const SKIP_KEYWORDS = [
    "SOURCE", "BR SSS", "TIMETABLE GENERATED", "MONDAY", "TUESDAY",
    "WEDNESDAY", "THURSDAY", "FRIDAY", "PERIOD", "MORNING BREAK",
    "LUNCH BREAK", "AFTERNOON", "SUMMARY", "PAGE", "GENERATED",
  ];

  function cleanName(raw) {
    if (raw == null || raw === "") return null;
    const parts = String(raw).split("\n");
    let result = parts[0];
    for (let i = 1; i < parts.length; i++) {
      const part = parts[i];
      if (!part) continue;
      const prevEnd = result.slice(-1) || "";
      const nextStart = part[0];
      if (/[a-z]/.test(nextStart)) result += part;
      else if (prevEnd === "-") result += part;
      else if (part === part.toUpperCase() && part.length <= 4) result += part;
      else result += " " + part;
    }
    result = result.replace(/\s+/g, " ").trim();
    return result || null;
  }

  function cleanCell(raw) {
    if (raw == null) return null;
    let text = String(raw).split(/\s+/).join(" ").trim();
    if (!text) return null;
    // Collapse split letters without lookbehind (older mobile Safari)
    text = text.replace(/(^|[^A-Za-z0-9_])([A-Z]) ([A-Z]) ([A-Z])(?![A-Za-z0-9_])/g, "$1$2$3$4");
    text = text.replace(/(^|[^A-Za-z0-9_])([A-Z]) ([A-Z])(?![A-Za-z0-9_])/g, "$1$2$3");
    return text;
  }

  function isFree(cellVal) {
    if (!cellVal) return true;
    return cellVal.trim().toUpperCase().startsWith("OFF");
  }

  function isTeaching(cellVal) {
    return Boolean(cellVal) && !isFree(cellVal);
  }

  function isOffCell(cellVal) {
    if (!cellVal) return false;
    return cellVal.trim().toUpperCase().startsWith("OFF");
  }

  function teachingDays(schedules, teacher) {
    const daysMap = schedules[teacher] || {};
    const out = new Set();
    for (const d of DAYS) {
      for (const p of PERIODS) {
        if (isTeaching((daysMap[d] || {})[p])) {
          out.add(d);
          break;
        }
      }
    }
    return out;
  }

  function replacementWorkingDays(schedules, teacher) {
    const td = teachingDays(schedules, teacher);
    if (td.size === 0) return ALL_DAYS;
    const onlyMwf = [...td].every((d) => MWF_DAYS.has(d)) &&
      ![...td].some((d) => TUTH_DAYS.has(d));
    const onlyTuTh = [...td].every((d) => TUTH_DAYS.has(d)) &&
      ![...td].some((d) => MWF_DAYS.has(d));
    if (onlyMwf) return MWF_DAYS;
    if (onlyTuTh) return TUTH_DAYS;
    return ALL_DAYS;
  }

  function isAvailableForCover(schedules, teacher, day, period) {
    const cell = (((schedules[teacher] || {})[day] || {})[period]);
    if (isTeaching(cell)) return false;
    if ((period === 8 || period === 9) && isOffCell(cell)) return false;
    return true;
  }

  function sheetToRows(sheet) {
    // Build dense 0-indexed rows from sheet range
    const ref = sheet["!ref"];
    if (!ref) return [];
    const range = XLSX.utils.decode_range(ref);
    const rows = [];
    for (let R = range.s.r; R <= range.e.r; R++) {
      const row = [];
      for (let C = range.s.c; C <= range.e.c; C++) {
        const addr = XLSX.utils.encode_cell({ r: R, c: C });
        const cell = sheet[addr];
        row.push(cell ? cell.v : null);
      }
      rows.push(row);
    }
    return rows;
  }

  function loadTimetableFromWorkbook(workbook) {
    const schedules = {};
    const teacherOrder = [];
    const seen = new Set();

    let pageSheets = workbook.SheetNames.filter((n) => n.startsWith("Page "));
    if (pageSheets.length === 0) pageSheets = [workbook.SheetNames[0]];

    for (const sheetName of pageSheets) {
      const sheet = workbook.Sheets[sheetName];
      const rows = sheetToRows(sheet);

      // Excel row 6 = index 5
      for (let i = ROW_DATA_START - 1; i < rows.length; i++) {
        const row = rows[i];
        if (!row || !row.some((c) => c != null && String(c).trim() !== "")) continue;

        let name = cleanName(row[0]);
        if (!name) continue;

        const nameUpper = name.toUpperCase();
        if (SKIP_KEYWORDS.some((kw) => nameUpper.includes(kw))) continue;
        if (/^\d+$/.test(nameUpper.replace(/\s/g, ""))) continue;
        if (["1", "2", "3", "4", "5", "6", "7", "8", "9",
             "MORNING BREAK", "LUNCH BREAK", "AFTERNOON BREAK",
             "AFTERNOON REGISTER"].includes(nameUpper)) continue;

        const base = name;
        let suffix = 2;
        while (seen.has(name)) {
          name = `${base} (${suffix})`;
          suffix += 1;
        }
        seen.add(name);
        teacherOrder.push(name);

        schedules[name] = {};
        for (const [day, startCol] of Object.entries(DAY_START_COLS)) {
          schedules[name][day] = {};
          for (const [periodStr, offset] of Object.entries(PERIOD_OFFSETS)) {
            const period = Number(periodStr);
            const colIdx = (startCol - 1) + offset;
            const val = colIdx < row.length ? row[colIdx] : null;
            schedules[name][day][period] = cleanCell(val);
          }
        }
      }
    }

    return { schedules, teacherOrder };
  }

  async function loadTimetable(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Could not load timetable (${res.status}).`);
    const buf = await res.arrayBuffer();
    const workbook = XLSX.read(buf, { type: "array", cellDates: false });
    return loadTimetableFromWorkbook(workbook);
  }

  function getWorkingPeriods(schedules, teacher, day) {
    const result = [];
    for (const p of PERIODS) {
      const cell = (((schedules[teacher] || {})[day] || {})[p]);
      if (isTeaching(cell)) result.push([p, cell]);
    }
    return result;
  }

  function getFreeTeachers(schedules, day, period, exclude) {
    exclude = exclude || new Set();
    return Object.keys(schedules)
      .filter((t) =>
        !exclude.has(t) &&
        replacementWorkingDays(schedules, t).has(day) &&
        isAvailableForCover(schedules, t, day, period)
      )
      .sort((a, b) => a.localeCompare(b));
  }

  function splitClassRoom(label) {
    if (!label) return ["", ""];
    const roomPattern =
      /\s+([AB]\s*\d+\.\d+\w*|Chem\s+L\s*\d*|C\s+(?:Phy|Bio|Com|WK|PE|Hindi|Hin)\s*\d*|A\s+Urdu\s+Rm|CDT\s*\d*|playground\s*\d*|Library\s+Rm|Audio|BIO\/MUSIC|B\s+\d+\.\d+\w*)\s*$/i;
    const m = label.match(roomPattern);
    if (m) {
      const idx = m.index;
      return [label.slice(0, idx).trim(), label.slice(idx).trim()];
    }
    return [label.trim(), ""];
  }

  global.DataLoader = {
    DAYS,
    PERIODS,
    loadTimetable,
    loadTimetableFromWorkbook,
    isTeaching,
    isFree,
    isOffCell,
    replacementWorkingDays,
    isAvailableForCover,
    getWorkingPeriods,
    getFreeTeachers,
    splitClassRoom,
  };
})(window);
