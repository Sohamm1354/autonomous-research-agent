import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useRef } from "react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export default function ReportViewer({ result, onReset }) {
  const reportRef = useRef(null);
  const charCount = result.final_report?.length || 0;
  const sources   = result.search_results?.length ?? "—";

  function copyReport() {
    navigator.clipboard.writeText(result.final_report);
    alert("Report copied to clipboard!");
  }

  async function downloadPDF() {
    const element = reportRef.current;
    if (!element) return;

    // Show loading state
    const btn = document.getElementById("pdf-btn");
    const original = btn.textContent;
    btn.textContent = "Generating PDF…";
    btn.disabled = true;

    try {
      const canvas = await html2canvas(element, {
        scale: 2,              // high resolution
        useCORS: true,
        backgroundColor: "#ffffff",
        logging: false,
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf     = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const pageWidth  = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin     = 15;
      const imgWidth   = pageWidth - margin * 2;
      const imgHeight  = (canvas.height * imgWidth) / canvas.width;

      // Add header
      pdf.setFontSize(10);
      pdf.setTextColor(136, 135, 128);
      pdf.text("Research Agent — Autonomous AI Research Report", margin, 10);
      pdf.text(new Date().toLocaleDateString(), pageWidth - margin, 10, { align: "right" });

      // Draw line under header
      pdf.setDrawColor(229, 227, 220);
      pdf.line(margin, 13, pageWidth - margin, 13);

      // If report fits in one page
      if (imgHeight + 20 <= pageHeight - margin) {
        pdf.addImage(imgData, "PNG", margin, 18, imgWidth, imgHeight);
      } else {
        // Multi-page handling
        let yOffset = 0;
        const contentHeight = pageHeight - margin - 18;

        while (yOffset < imgHeight) {
          if (yOffset > 0) {
            pdf.addPage();
            // Repeat header on each page
            pdf.setFontSize(10);
            pdf.setTextColor(136, 135, 128);
            pdf.text("Research Agent — Autonomous AI Research Report", margin, 10);
            pdf.line(margin, 13, pageWidth - margin, 13);
          }

          pdf.addImage(
            imgData, "PNG",
            margin,
            18 - yOffset * (imgWidth / canvas.width) * (canvas.height / imgHeight),
            imgWidth,
            imgHeight,
            undefined,
            "FAST"
          );

          yOffset += contentHeight * (canvas.width / imgWidth);
        }
      }

      // Footer on last page
      const totalPages = pdf.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i);
        pdf.setFontSize(9);
        pdf.setTextColor(136, 135, 128);
        pdf.text(
          `Page ${i} of ${totalPages}`,
          pageWidth / 2,
          pageHeight - 8,
          { align: "center" }
        );
      }

      // Generate filename from question
      const filename = (result.question || "research-report")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .slice(0, 50);

      pdf.save(`${filename}.pdf`);

    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("PDF generation failed. Try the Copy button instead.");
    } finally {
      btn.textContent = original;
      btn.disabled = false;
    }
  }

  return (
    <div>
      {/* Stats row */}
      <div className="stat-row">
        <div className="stat">
          <div className="stat-val">{sources}</div>
          <div className="stat-lab">Sources used</div>
        </div>
        <div className="stat">
          <div className="stat-val">{Math.round(result.elapsed_sec)}s</div>
          <div className="stat-lab">Time taken</div>
        </div>
        <div className="stat">
          <div className="stat-val">{(charCount / 1000).toFixed(1)}k</div>
          <div className="stat-lab">Report length</div>
        </div>
        <div className="stat">
          <div className="stat-val">$0.00</div>
          <div className="stat-lab">Cost</div>
        </div>
      </div>

      {/* Report card */}
      <div className="card">
        {/* Action buttons */}
        <div className="action-row" style={{ marginBottom: "1rem" }}>
          <p className="section-label" style={{ margin: 0 }}>Report</p>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn" onClick={copyReport}>
              Copy
            </button>
            <button
              id="pdf-btn"
              className="btn primary"
              onClick={downloadPDF}
            >
              ↓ Download PDF
            </button>
          </div>
        </div>

        {/* Report content — this is what gets captured for PDF */}
        <div ref={reportRef} className="report-pdf-wrapper">
          {/* PDF title block */}
          <div className="pdf-title-block">
            <h1 className="pdf-question">{result.question}</h1>
            <p className="pdf-meta">
              Generated by Research Agent · {new Date().toLocaleDateString()} ·
              {sources} sources · {Math.round(result.elapsed_sec)}s
            </p>
          </div>

          {/* Markdown report */}
          <div className="report-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.final_report}
            </ReactMarkdown>
          </div>

          {/* Reflection */}
          {result.reflection && (
            <div style={{ marginTop: "1.5rem" }}>
              <p className="section-label">Research gaps identified</p>
              <div className="reflection-box">{result.reflection}</div>
            </div>
          )}
        </div>

        {/* Failed sources — outside PDF capture */}
        {result.failed_urls?.length > 0 && (
          <>
            <div className="divider" style={{ margin: "1rem 0" }} />
            <p className="section-label">Failed sources</p>
            <p className="meta">{result.failed_urls.join(", ")}</p>
          </>
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem" }}>
        <button className="btn" onClick={onReset}>↺ New research</button>
      </div>
    </div>
  );
}