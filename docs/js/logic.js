/**
 * Session state + replacement lookup - port of replacement_logic.py
 */
(function (global) {
  "use strict";

  const DL = () => global.DataLoader;

  function buildSession(schedules, day, absentTeachers) {
    const session = {
      day,
      absent_teachers: [...absentTeachers],
      assignments: {},
      working_periods: {},
    };

    for (const teacher of absentTeachers) {
      const wps = DL().getWorkingPeriods(schedules, teacher, day);
      session.working_periods[teacher] = wps;
      session.assignments[teacher] = {};
      for (const [p] of wps) session.assignments[teacher][p] = null;
    }
    return session;
  }

  function committedForPeriod(session, period, currentAbsent) {
    const committed = new Set();
    for (const [absentT, periodMap] of Object.entries(session.assignments)) {
      if (absentT === currentAbsent) continue;
      const replacer = periodMap[period];
      if (replacer) committed.add(replacer);
    }
    return committed;
  }

  function availableReplacements(schedules, session, absentTeacher, period) {
    const exclude = new Set(session.absent_teachers);
    for (const t of committedForPeriod(session, period, absentTeacher)) {
      exclude.add(t);
    }
    return DL().getFreeTeachers(schedules, session.day, period, exclude);
  }

  function assignReplacement(session, absentTeacher, period, replacingTeacher) {
    if (session.assignments[absentTeacher]) {
      session.assignments[absentTeacher][period] = replacingTeacher || null;
    }
  }

  function summaryRows(session) {
    const rows = [];
    for (const teacher of session.absent_teachers) {
      for (const [period, classLabel] of session.working_periods[teacher] || []) {
        rows.push({
          absent: teacher,
          period,
          class: classLabel || "",
          replacer: (session.assignments[teacher] || {})[period] || null,
        });
      }
    }
    return rows;
  }

  function sessionComplete(session) {
    for (const teacher of session.absent_teachers) {
      for (const [period] of session.working_periods[teacher] || []) {
        if (!(session.assignments[teacher] || {})[period]) return false;
      }
    }
    return true;
  }

  function unassignedCount(session) {
    let n = 0;
    for (const teacher of session.absent_teachers) {
      for (const [period] of session.working_periods[teacher] || []) {
        if (!(session.assignments[teacher] || {})[period]) n += 1;
      }
    }
    return n;
  }

  global.ReplacementLogic = {
    buildSession,
    availableReplacements,
    assignReplacement,
    summaryRows,
    sessionComplete,
    unassignedCount,
  };
})(window);
