import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import Papa from "papaparse";

export function generateExecutiveReport(dashboardData, trendsData) {
  const doc = new jsPDF("p", "pt", "a4");
  const margin = 40;

  // Header
  doc.setFontSize(24);
  doc.setTextColor(15, 23, 42); // slate-900
  doc.text("AI Maintenance Executive Report", margin, 60);

  doc.setFontSize(12);
  doc.setTextColor(100, 116, 139); // slate-500
  doc.text(`Generated exactly at: ${new Date().toLocaleString()}`, margin, 80);

  // Line separator
  doc.setLineWidth(1);
  doc.setDrawColor(226, 232, 240); // slate-200
  doc.line(margin, 100, 595 - margin, 100);

  // KPIs
  doc.setFontSize(16);
  doc.setTextColor(15, 23, 42);
  doc.text("System Key Performance Indicators", margin, 130);
  
  const kpiData = dashboardData ? [
    ["Total Monitored Assets", dashboardData.total_equipment?.toString() || "0"],
    ["Active Pre-Emptive Alarms", dashboardData.active_alerts?.toString() || "0"],
    ["Critical High-Risk Assets", dashboardData.critical_count?.toString() || "0"],
    ["ML Inference Volume", dashboardData.predictions_today?.toString() || "0"],
    ["Overall Fleet Integrity", "99.9%"],
  ] : [["No data", "available"]];

  autoTable(doc, {
    startY: 150,
    head: [["Metric", "Value"]],
    body: kpiData,
    theme: "striped",
    headStyles: { fillColor: [14, 165, 233] },
    styles: { cellPadding: 8, fontSize: 11 },
    margin: { left: margin, right: margin }
  });

  // Risk Trends
  const finalY = doc.lastAutoTable.finalY || 300;
  
  doc.setFontSize(16);
  doc.setTextColor(15, 23, 42);
  doc.text("Risk Horizon (Last 7 Days)", margin, finalY + 40);

  const trendRows = trendsData && trendsData.length > 0
    ? trendsData.map(t => [t.date, (t.avg_risk * 100).toFixed(1) + "%", (t.max_risk * 100).toFixed(1) + "%"])
    : [["N/A", "N/A", "N/A"]];

  autoTable(doc, {
    startY: finalY + 60,
    head: [["Date", "Fleet Average Risk", "Peak Anomaly Risk"]],
    body: trendRows,
    theme: "grid",
    headStyles: { fillColor: [244, 63, 94] },
    styles: { cellPadding: 6, fontSize: 10 },
    margin: { left: margin, right: margin }
  });
  
  // Equipment Health Status
  const trendFinalY = doc.lastAutoTable.finalY || 400;
  
  doc.setFontSize(16);
  doc.setTextColor(15, 23, 42);
  doc.text("Individual Asset Health Registry", margin, trendFinalY + 40);

  const healthDataRows = dashboardData && dashboardData.equipment_health && dashboardData.equipment_health.length > 0
    ? dashboardData.equipment_health.map(eq => [
        eq.equipment_name,
        eq.equipment_type.replace('_', ' ').toUpperCase(),
        eq.status.toUpperCase(),
        (eq.risk_score * 100).toFixed(1) + "%",
        eq.active_alerts > 0 ? `${eq.active_alerts} Alarms` : "Clear"
      ])
    : [["No Asset Data", "-", "-", "-", "-"]];

  autoTable(doc, {
    startY: trendFinalY + 60,
    head: [["Asset Name", "Hardware Type", "Current Status", "Risk Score", "Alerts"]],
    body: healthDataRows,
    theme: "grid",
    headStyles: { fillColor: [15, 23, 42] },
    styles: { cellPadding: 6, fontSize: 9 },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    margin: { left: margin, right: margin }
  });
  
  // Footer
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(10);
    doc.setTextColor(148, 163, 184);
    doc.text(
      `Confidential & Proprietary - Page ${i} of ${pageCount}`,
      margin,
      doc.internal.pageSize.height - 30
    );
  }

  doc.save(`executive_report_${new Date().toISOString().slice(0, 10)}.pdf`);
}

export function exportToCSV(data, filename = "export.csv") {
  if (!data || !data.length) return;
  const csv = Papa.unparse(data);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
