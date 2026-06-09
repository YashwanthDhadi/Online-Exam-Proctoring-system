"""
report_generator.py  (extended for exam proctoring)
Original generate_pdf_report() kept for study sessions.
New generate_exam_report() produces the Exam Integrity Report with evidence screenshots.
"""
import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')


# ─────────────────────────────────────────────────────────────────
# NEW: Exam Integrity Report
# ─────────────────────────────────────────────────────────────────

def generate_exam_report(student_id, exam_id, started_at, duration_secs,
                          violations: dict, risk_score: int, risk_level: str,
                          ai_summary: str, evidence_files: list) -> str:
    """
    Generate a PDF exam integrity report.
    Falls back to a plain-text report if reportlab is not installed.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    duration_mins = max(1, duration_secs // 60)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"exam_{student_id}_{exam_id}_{timestamp}"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, Image as RLImage,
                                        HRFlowable)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        pdf_path = os.path.join(REPORTS_DIR, filename + ".pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # ── Title ─────────────────────────────────────────────
        title_style = ParagraphStyle('ETitle', parent=styles['Title'],
                                     fontSize=22,
                                     textColor=colors.HexColor('#1a1a2e'))
        story.append(Paragraph("Exam Integrity Report", title_style))
        story.append(HRFlowable(width="100%", thickness=2,
                                color=colors.HexColor('#6c63ff')))
        story.append(Spacer(1, 0.3*cm))

        # ── Meta info ─────────────────────────────────────────
        info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                    fontSize=11,
                                    textColor=colors.HexColor('#555555'))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}  |  "
            f"Student ID: <b>{student_id}</b>  |  Exam ID: <b>{exam_id}</b>",
            info_style))
        story.append(Spacer(1, 0.5*cm))

        # ── Summary table ─────────────────────────────────────
        risk_color = (
            colors.HexColor('#00a854') if risk_level == 'Low' else
            colors.HexColor('#d4880e') if risk_level == 'Medium' else
            colors.HexColor('#e83c4a')
        )
        kpi_data = [
            ['Field', 'Value'],
            ['Exam Start',     started_at or 'N/A'],
            ['Duration',       f"{duration_mins} minutes"],
            ['Risk Score',     str(risk_score)],
            ['Risk Level',     risk_level],
        ]
        table = Table(kpi_data, colWidths=[8*cm, 9*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f0f4ff'), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING',     (0, 0), (-1, -1), 8),
            ('TEXTCOLOR',   (1, 4), (1, 4), risk_color),
            ('FONTNAME',    (1, 4), (1, 4), 'Helvetica-Bold'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.6*cm))

        # ── Violations table ──────────────────────────────────
        story.append(Paragraph("Violations Detected", styles['Heading2']))
        vio_labels = {
            'face_missing':   'Face Missing',
            'multiple_faces': 'Multiple Faces',
            'looking_away':   'Looking Away',
            'window_switch':  'Window Switch',
            'inactivity':     'Long Inactivity',
        }
        vio_data = [['Violation Type', 'Count']]
        for key, label in vio_labels.items():
            vio_data.append([label, str(violations.get(key, 0))])

        vio_table = Table(vio_data, colWidths=[10*cm, 7*cm])
        vio_table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#6c63ff')),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f8f0ff'), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING',     (0, 0), (-1, -1), 8),
        ]))
        story.append(vio_table)
        story.append(Spacer(1, 0.6*cm))

        # ── AI Summary ────────────────────────────────────────
        if ai_summary:
            story.append(Paragraph("AI Integrity Analysis", styles['Heading2']))
            body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                        fontSize=11, leading=16,
                                        textColor=colors.HexColor('#333333'))
            story.append(Paragraph(ai_summary, body_style))
            story.append(Spacer(1, 0.6*cm))

        # ── Evidence screenshots ──────────────────────────────
        valid_evidence = [f for f in evidence_files if os.path.isfile(f)]
        if valid_evidence:
            story.append(Paragraph("Evidence Screenshots", styles['Heading2']))
            for ev_path in valid_evidence[:10]:   # cap at 10 images per report
                fname = os.path.basename(ev_path)
                story.append(Paragraph(fname,
                    ParagraphStyle('EvidFname', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.grey)))
                try:
                    img = RLImage(ev_path, width=10*cm, height=7.5*cm)
                    story.append(img)
                except Exception:
                    story.append(Paragraph("[Image could not be loaded]",
                        ParagraphStyle('Err', parent=styles['Normal'],
                                       textColor=colors.red)))
                story.append(Spacer(1, 0.3*cm))

        # ── Footer ────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor('#cccccc')))
        story.append(Paragraph(
            "Generated by AI-Based Online Exam Proctoring System",
            ParagraphStyle('Footer', parent=styles['Normal'],
                           fontSize=9, textColor=colors.grey)))

        doc.build(story)
        return pdf_path

    except ImportError:
        # Plain text fallback
        txt_path = os.path.join(REPORTS_DIR, filename + ".txt")
        with open(txt_path, 'w') as f:
            f.write("EXAM INTEGRITY REPORT\n")
            f.write("=" * 45 + "\n")
            f.write(f"Generated : {datetime.now().strftime('%B %d, %Y %H:%M')}\n")
            f.write(f"Student ID: {student_id}\n")
            f.write(f"Exam ID   : {exam_id}\n")
            f.write(f"Duration  : {duration_mins} minutes\n")
            f.write(f"Risk Score: {risk_score}\n")
            f.write(f"Risk Level: {risk_level}\n\n")
            f.write("VIOLATIONS:\n")
            for k, v in violations.items():
                f.write(f"  {k.replace('_', ' ').title()}: {v}\n")
            if ai_summary:
                f.write(f"\nAI SUMMARY:\n{ai_summary}\n")
            if evidence_files:
                f.write("\nEVIDENCE FILES:\n")
                for ev in evidence_files:
                    f.write(f"  {os.path.basename(ev)}\n")
        return txt_path


# ─────────────────────────────────────────────────────────────────
# Original study session PDF (unchanged)
# ─────────────────────────────────────────────────────────────────

def generate_pdf_report(subject, duration_mins, focus_pct, stats, ai_report, history):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"session_{subject.replace(' ', '_')}_{timestamp}"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        pdf_path = os.path.join(REPORTS_DIR, filename + ".pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=22,
                                     textColor=colors.HexColor('#1a1a2e'))
        story.append(Paragraph("Smart Study — Session Report", title_style))
        story.append(Spacer(1, 0.3*cm))

        info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                    fontSize=11,
                                    textColor=colors.HexColor('#555555'))
        story.append(Paragraph(
            f"Date: {datetime.now().strftime('%B %d, %Y %H:%M')}  |  Subject: {subject}",
            info_style))
        story.append(Spacer(1, 0.5*cm))

        kpi_data = [
            ['Metric', 'Value'],
            ['Duration', f"{duration_mins} minutes"],
            ['Focus Score', f"{focus_pct}%"],
        ]
        for k, v in stats.items():
            kpi_data.append([k, f"{v}%"])
        table = Table(kpi_data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f0f4ff'), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING',     (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.7*cm))

        if ai_report:
            story.append(Paragraph("AI Coach Feedback", styles['Heading2']))
            body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                        fontSize=11, leading=16,
                                        textColor=colors.HexColor('#333333'))
            story.append(Paragraph(ai_report, body_style))
            story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("Generated by Smart Study Student Analyzer",
            ParagraphStyle('Footer', parent=styles['Normal'],
                           fontSize=9, textColor=colors.grey)))
        doc.build(story)
        return pdf_path

    except ImportError:
        txt_path = os.path.join(REPORTS_DIR, filename + ".txt")
        with open(txt_path, 'w') as f:
            f.write("SMART STUDY — SESSION REPORT\n" + "=" * 40 + "\n")
            f.write(f"Date: {datetime.now().strftime('%B %d, %Y %H:%M')}\n")
            f.write(f"Subject: {subject}\nDuration: {duration_mins} minutes\n")
            f.write(f"Focus Score: {focus_pct}%\n\nSTATS:\n")
            for k, v in stats.items():
                f.write(f"  {k}: {v}%\n")
            if ai_report:
                f.write(f"\nAI COACH FEEDBACK:\n{ai_report}\n")
        return txt_path
