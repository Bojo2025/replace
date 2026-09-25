/**
 * BR SSS Teacher Replacement - web UI (mobile + desktop)
 */
(function () {
  "use strict";

  const TIMETABLE_URL = "data/latest-20-april.xlsx";

  let schedules = null;
  let teacherOrder = [];
  let selectedDay = "Monday";
  let absentSelected = new Set();
  let session = null;
  let teacherIdx = 0;
  let currentStep = 1; // 1 select, 2 assign, 3 review

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), 2200);
  }

  function showScreen(id) {
    $$(".screen").forEach((s) => s.classList.remove("active"));
    $(`#${id}`).classList.add("active");
  }

  function setSteps(step) {
    currentStep = step;
    $$(".step-pill").forEach((el) => {
      const n = Number(el.dataset.step);
      el.classList.toggle("active", n === step);
      el.classList.toggle("done", n < step);
    });
    const crumbs = {
      1: "Select day & absent teachers",
      2: "Assign replacements",
      3: "Review & export PDF",
    };
    $("#crumb").textContent = crumbs[step] || "";
    const dayBadge = $("#day-badge");
    if (step >= 2 && session) {
      dayBadge.style.display = "";
      dayBadge.textContent = session.day;
    } else if (step === 1) {
      dayBadge.style.display = "none";
    }
  }

  function setBottomBar(buttons) {
    const bar = $("#bottom-bar");
    bar.innerHTML = "";
    for (const b of buttons) {
      const btn = document.createElement("button");
      btn.className = `btn ${b.cls || "btn-primary"}`;
      btn.textContent = b.label;
      if (b.disabled) btn.disabled = true;
      btn.addEventListener("click", b.onClick);
      bar.appendChild(btn);
    }
  }

  // --- Screen 1 ---

  function teachersForDay(day) {
    return teacherOrder.filter((t) =>
      DataLoader.replacementWorkingDays(schedules, t).has(day)
    );
  }

  function renderDayButtons() {
    const grid = $("#day-grid");
    grid.innerHTML = "";
    for (const day of DataLoader.DAYS) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "day-btn" + (day === selectedDay ? " selected" : "");
      btn.textContent = day.slice(0, 3);
      btn.title = day;
      btn.addEventListener("click", () => {
        selectedDay = day;
        absentSelected.clear();
        renderDayButtons();
        renderTeacherList();
        updateAbsentCount();
      });
      grid.appendChild(btn);
    }
  }

  function renderTeacherList() {
    const list = $("#teacher-list");
    const q = ($("#search-input").value || "").trim().toUpperCase();
    const teachers = teachersForDay(selectedDay).filter((t) =>
      !q || t.toUpperCase().includes(q)
    );

    list.innerHTML = "";
    if (!teachers.length) {
      list.innerHTML = `<div class="empty-periods">No teachers work on ${selectedDay}.</div>`;
      return;
    }

    for (const name of teachers) {
      const item = document.createElement("label");
      item.className = "teacher-item" + (absentSelected.has(name) ? " checked" : "");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = absentSelected.has(name);
      cb.addEventListener("change", () => {
        if (cb.checked) absentSelected.add(name);
        else absentSelected.delete(name);
        item.classList.toggle("checked", cb.checked);
        updateAbsentCount();
      });
      const span = document.createElement("span");
      span.className = "teacher-name";
      span.textContent = name;
      item.appendChild(cb);
      item.appendChild(span);
      list.appendChild(item);
    }
  }

  function updateAbsentCount() {
    const n = absentSelected.size;
    $("#absent-count").textContent =
      n === 0 ? "No teachers marked absent" :
      n === 1 ? "1 teacher marked absent" :
      `${n} teachers marked absent`;
    const next = $("#btn-next-select");
    if (next) next.disabled = n === 0;
  }

  function goToSelect() {
    setSteps(1);
    showScreen("screen-select");
    renderDayButtons();
    renderTeacherList();
    updateAbsentCount();
    setBottomBar([
      {
        label: "Next: Assign ->",
        cls: "btn-primary",
        disabled: absentSelected.size === 0,
        onClick: () => {
          if (!absentSelected.size) {
            toast("Select at least one absent teacher");
            return;
          }
          // Preserve selection order as shown in list for this day
          const ordered = teachersForDay(selectedDay).filter((t) =>
            absentSelected.has(t)
          );
          session = ReplacementLogic.buildSession(schedules, selectedDay, ordered);
          teacherIdx = 0;
          goToAssign();
        },
      },
    ]);
    // Keep a stable id for disable toggle
    const btn = $("#bottom-bar .btn");
    if (btn) btn.id = "btn-next-select";
  }

  // --- Screen 2 ---

  function goToAssign() {
    setSteps(2);
    showScreen("screen-assign");
    renderAssign();
  }

  function renderAssign() {
    const absent = session.absent_teachers[teacherIdx];
    const total = session.absent_teachers.length;
    const pct = ((teacherIdx) / Math.max(total, 1)) * 100;

    $("#progress-fill").style.width = `${pct + (100 / total) * 0.15}%`;
    $("#progress-label").textContent =
      `Teacher ${teacherIdx + 1} of ${total}`;
    $("#absent-name").textContent = absent;

    const wps = session.working_periods[absent] || [];
    const container = $("#period-list");
    container.innerHTML = "";

    if (!wps.length) {
      container.innerHTML =
        `<div class="empty-periods">No teaching periods on ${session.day} for this teacher.</div>`;
    } else {
      for (const [period, classLabel] of wps) {
        const options = ReplacementLogic.availableReplacements(
          schedules, session, absent, period
        );
        const current = (session.assignments[absent] || {})[period] || "";
        const [cls, room] = DataLoader.splitClassRoom(classLabel);

        const card = document.createElement("div");
        card.className = "period-card";

        const top = document.createElement("div");
        top.className = "period-top";

        const badge = document.createElement("div");
        badge.className = "period-badge";
        badge.textContent = String(period);

        const info = document.createElement("div");
        info.className = "period-info";
        info.innerHTML =
          `<div class="period-class">${escapeHtml(cls || classLabel)}</div>` +
          (room ? `<div class="period-room">${escapeHtml(room)}</div>` : "");

        const pill = document.createElement("div");
        pill.className = "avail-pill";
        pill.textContent = `${options.length} free`;

        top.appendChild(badge);
        top.appendChild(info);
        top.appendChild(pill);

        const select = document.createElement("select");
        select.className = "period-select" + (current ? " has-value" : "");
        select.innerHTML =
          `<option value="">- Select replacement -</option>` +
          options
            .map(
              (t) =>
                `<option value="${escapeAttr(t)}"${t === current ? " selected" : ""}>${escapeHtml(t)}</option>`
            )
            .join("");

        // Keep previously selected teacher even if temporarily not in list
        if (current && !options.includes(current)) {
          const opt = document.createElement("option");
          opt.value = current;
          opt.selected = true;
          opt.textContent = current + " (busy?)";
          select.appendChild(opt);
        }

        select.addEventListener("change", () => {
          const val = select.value || null;
          ReplacementLogic.assignReplacement(session, absent, period, val);
          select.classList.toggle("has-value", Boolean(val));
          // Re-render so other period dropdowns update (double-booking)
          renderAssign();
        });

        card.appendChild(top);
        card.appendChild(select);
        container.appendChild(card);
      }
    }

    const isFirst = teacherIdx === 0;
    const isLast = teacherIdx >= session.absent_teachers.length - 1;

    setBottomBar([
      {
        label: isFirst ? "<- Back" : "<- Previous",
        cls: "btn-secondary",
        onClick: () => {
          if (isFirst) goToSelect();
          else {
            teacherIdx -= 1;
            renderAssign();
          }
        },
      },
      {
        label: isLast ? "Review ->" : "Next teacher ->",
        cls: "btn-primary",
        onClick: () => {
          if (isLast) goToReview();
          else {
            teacherIdx += 1;
            renderAssign();
          }
        },
      },
    ]);
  }

  // --- Screen 3 ---

  function goToReview() {
    setSteps(3);
    showScreen("screen-review");
    renderReview();
  }

  function renderReview() {
    const rows = ReplacementLogic.summaryRows(session);
    const unassigned = ReplacementLogic.unassignedCount(session);
    const chips = $("#summary-chips");
    chips.innerHTML = `
      <span class="chip">${session.day}</span>
      <span class="chip danger">${session.absent_teachers.length} absent</span>
      <span class="chip">${rows.length} periods</span>
      <span class="chip ${unassigned ? "warn" : "success"}">${
        unassigned ? unassigned + " unassigned" : "All assigned"
      }</span>
    `;

    const container = $("#review-groups");
    container.innerHTML = "";

    for (const teacher of session.absent_teachers) {
      const teacherRows = rows.filter((r) => r.absent === teacher);
      const group = document.createElement("div");
      group.className = "review-group";
      group.innerHTML = `<div class="review-group-head">${escapeHtml(teacher)}</div>`;

      const table = document.createElement("table");
      table.className = "review-table";
      table.innerHTML = `
        <thead><tr>
          <th>Period</th><th>Class</th><th>Room</th><th>Replaced by</th>
        </tr></thead>
        <tbody></tbody>
      `;
      const tbody = table.querySelector("tbody");
      for (const r of teacherRows) {
        const [cls, room] = DataLoader.splitClassRoom(r.class);
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${r.period}</td>
          <td>${escapeHtml(cls || r.class)}</td>
          <td>${escapeHtml(room)}</td>
          <td class="${r.replacer ? "replacer-ok" : "replacer-miss"}">${
            r.replacer ? escapeHtml(r.replacer) : "- Unassigned -"
          }</td>
        `;
        tbody.appendChild(tr);
      }
      if (!teacherRows.length) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="4" style="color:var(--muted)">No teaching periods</td>`;
        tbody.appendChild(tr);
      }
      group.appendChild(table);
      container.appendChild(group);
    }

    setBottomBar([
      {
        label: "<- Edit",
        cls: "btn-secondary",
        onClick: () => {
          teacherIdx = 0;
          goToAssign();
        },
      },
      {
        label: "Download PDF",
        cls: "btn-success",
        onClick: () => {
          try {
            PdfExport.generatePdf(session);
            toast("PDF downloaded");
          } catch (err) {
            console.error(err);
            toast("PDF failed: " + err.message);
          }
        },
      },
    ]);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  // --- Boot ---

  async function boot() {
    $("#search-input").addEventListener("input", renderTeacherList);
    $("#btn-select-all").addEventListener("click", () => {
      const q = ($("#search-input").value || "").trim().toUpperCase();
      for (const t of teachersForDay(selectedDay)) {
        if (!q || t.toUpperCase().includes(q)) absentSelected.add(t);
      }
      renderTeacherList();
      updateAbsentCount();
    });
    $("#btn-clear-all").addEventListener("click", () => {
      absentSelected.clear();
      renderTeacherList();
      updateAbsentCount();
    });
    $("#btn-start-over").addEventListener("click", () => {
      if (confirm("Start over? Current assignments will be cleared.")) {
        session = null;
        absentSelected.clear();
        teacherIdx = 0;
        goToSelect();
      }
    });

    try {
      const data = await DataLoader.loadTimetable(TIMETABLE_URL);
      schedules = data.schedules;
      teacherOrder = data.teacherOrder;
      $("#loading-screen").style.display = "none";
      $("#app-main").style.display = "flex";
      $("#topbar-sub").textContent =
        `Timetable: ${teacherOrder.length} teachers loaded`;
      goToSelect();
    } catch (err) {
      console.error(err);
      $("#loading-msg").textContent = "Failed to load timetable";
      $("#loading-error").textContent =
        err.message +
        " - open this site via a local server or GitHub Pages (file:// cannot fetch the Excel).";
      $("#loading-error").style.display = "block";
      $(".spinner").style.display = "none";
    }
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
