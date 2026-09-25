/**
 * PDF export using jsPDF + autoTable (browser)
 */
(function (global) {
  "use strict";

  function generatePdf(session) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const pageW = doc.internal.pageSize.getWidth();
    const day = session.day || "";
    const absentList = session.absent_teachers || [];
    const now = new Date();
    const dateStr = now.toLocaleDateString("en-GB", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
    const genStr = now.toLocaleString("en-GB", {
      day: "numeric", month: "long", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });

    const HEADER_BG = [26, 35, 126];
    const PRIMARY = [21, 101, 192];
    const SUCCESS = [46, 125, 50];
    const WARNING = [230, 81, 0];

    function drawHeaderFooter() {
      const pageCount = doc.internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        // header
        doc.setFillColor(...HEADER_BG);
        doc.rect(0, 0, pageW, 18, "F");
        doc.setTextColor(144, 202, 249);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(8);
        doc.text("BR SSS", 14, 8);
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(13);
        doc.text("TEACHER REPLACEMENT SHEET", pageW / 2, 9, { align: "center" });
        doc.setTextColor(144, 202, 249);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(8);
        doc.text(dateStr, pageW - 14, 8, { align: "right" });

        doc.setFillColor(...PRIMARY);
        doc.rect(0, 18, pageW, 7, "F");
        doc.setTextColor(255, 255, 255);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(9);
        doc.text(`Day:  ${day}`, pageW / 2, 22.5, { align: "center" });

        // footer
        doc.setTextColor(100, 116, 139);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(7.5);
        doc.text(
          `Generated: ${genStr}  -  BR SSS Replacement System`,
          14,
          287
        );
        doc.text(`Page ${i}`, pageW - 14, 287, { align: "right" });
      }
    }

    let y = 32;
    doc.setTextColor(100, 116, 139);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("ABSENT TEACHERS", 14, y);
    y += 4;

    const absentBody = absentList.map((teacher, idx) => {
      const working = session.working_periods[teacher] || [];
      const periods = working.length
        ? working.map(([p]) => p).join(", ")
        : "None";
      return [String(idx + 1), teacher, periods];
    });

    doc.autoTable({
      startY: y,
      head: [["#", "Teacher Name", "Periods Teaching"]],
      body: absentBody,
      styles: { fontSize: 9, cellPadding: 3 },
      headStyles: { fillColor: [227, 242, 253], textColor: PRIMARY, fontStyle: "bold" },
      margin: { left: 14, right: 14 },
      theme: "grid",
    });

    y = doc.lastAutoTable.finalY + 10;
    doc.setTextColor(100, 116, 139);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("REPLACEMENT SCHEDULE", 14, y);
    y += 4;

    const rows = global.ReplacementLogic.summaryRows(session);

    for (const teacher of absentList) {
      const teacherRows = rows.filter((r) => r.absent === teacher);
      if (!teacherRows.length) continue;

      if (y > 250) {
        doc.addPage();
        y = 32;
      }

      doc.setFillColor(255, 235, 238);
      doc.roundedRect(14, y, pageW - 28, 8, 1, 1, "F");
      doc.setTextColor(30, 41, 59);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.text(teacher, 18, y + 5.5);
      y += 10;

      const body = teacherRows.map((r) => {
        const [cls, room] = global.DataLoader.splitClassRoom(r.class);
        return [
          `Period ${r.period}`,
          cls || r.class,
          room,
          r.replacer || "- Unassigned -",
        ];
      });

      doc.autoTable({
        startY: y,
        head: [["Period", "Class / Subject", "Room", "Replaced By"]],
        body,
        styles: { fontSize: 9, cellPadding: 2.5 },
        headStyles: { fillColor: [238, 242, 247], textColor: [100, 116, 139], fontStyle: "bold" },
        columnStyles: {
          0: { cellWidth: 22 },
          2: { cellWidth: 28 },
          3: { cellWidth: 45 },
        },
        didParseCell(data) {
          if (data.section === "body" && data.column.index === 3) {
            const val = data.cell.raw;
            if (val && !String(val).includes("Unassigned")) {
              data.cell.styles.textColor = SUCCESS;
              data.cell.styles.fontStyle = "bold";
              data.cell.styles.fillColor = [232, 245, 233];
            } else {
              data.cell.styles.textColor = WARNING;
              data.cell.styles.fontStyle = "italic";
              data.cell.styles.fillColor = [255, 243, 224];
            }
          }
        },
        margin: { left: 14, right: 14 },
        theme: "grid",
      });

      y = doc.lastAutoTable.finalY + 8;
    }

    drawHeaderFooter();

    const safeDay = day.replace(/\s+/g, "_");
    const iso = now.toISOString().slice(0, 10);
    doc.save(`Replacement_${safeDay}_${iso}.pdf`);
  }

  global.PdfExport = { generatePdf };
})(window);
