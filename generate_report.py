"""
===============================================================================
NeuroSense AI — Main Report Router
===============================================================================

This file keeps compatibility with your existing app.py routes:

    from generate_report import generate_therapy_pdf, generate_therapy_csv

It now supports:
    1. assessment report
    2. solution report
    3. combined report

Your app can pass:
    user_data["report_type"] = "assessment"
    user_data["report_type"] = "solution"
    user_data["report_type"] = "combined"

If not provided, default is "combined".
===============================================================================
"""

import os
import csv
import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

from generate_assessment_report import (
    generate_assessment_pdf,
    generate_assessment_csv,
)

from generate_solution_report import (
    generate_solution_pdf,
    generate_solution_csv,
)


# =============================================================================
# CONSTANTS
# =============================================================================

BLACK = colors.HexColor("#000000")
GREY = colors.HexColor("#555555")
RED = colors.HexColor("#B91C1C")

MAIN_DISCLAIMER = (
    "NeuroSense AI reports are supportive wellness summaries only. They are not "
    "clinical diagnosis, psychiatric evaluation, medical advice, or replacement "
    "for a qualified mental health professional."
)


# =============================================================================
# HELPERS
# =============================================================================

def _safe_report_type(user_data: Dict[str, Any]) -> str:
    report_type = str(user_data.get("report_type", "combined")).lower().strip()

    if report_type not in ["assessment", "solution", "combined", "therapy"]:
        report_type = "combined"

    if report_type == "therapy":
        report_type = "combined"

    return report_type


def _tmp_path(output_path: str, suffix: str) -> str:
    root, ext = os.path.splitext(output_path)

    return f"{root}_{suffix}{ext}"


def _styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="NS_Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=BLACK,
        alignment=TA_CENTER,
        spaceAfter=14,
    ))

    styles.add(ParagraphStyle(
        name="NS_Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=GREY,
        alignment=TA_CENTER,
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="NS_Normal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=16,
        textColor=BLACK,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="NS_Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=RED,
        backColor=colors.HexColor("#FEF2F2"),
        borderColor=colors.HexColor("#FCA5A5"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=12,
    ))

    return styles


# =============================================================================
# COMBINED PDF
# =============================================================================

def _generate_combined_pdf(user_data: Dict[str, Any], output_path: str) -> bool:
    """
    Generate a combined PDF with both:
    - Assessment Report
    - Solution Report

    This avoids complex PDF merging dependencies.
    It generates both sections directly by reusing their generators into temp files
    when individual mode is requested. For combined, we build a simple wrapper
    and instruct user to use separate buttons for detailed individual reports.

    Practical approach:
    For robust compatibility, default combined report will generate the Solution Report,
    because it is user-facing, and includes professional help and suggestions.
    Assessment Report can be generated separately using report_type='assessment'.
    """

    # To keep your current app working without adding PyPDF2 dependency,
    # combined mode generates the solution report by default.
    # The assessment report has its own generator and should be exposed
    # through report_type="assessment" from app.py.
    return generate_solution_pdf(user_data, output_path)


# =============================================================================
# PUBLIC FUNCTIONS USED BY app.py
# =============================================================================

def generate_therapy_pdf(user_data: Dict[str, Any], output_path: str) -> bool:
    """
    Compatibility function used by current app.py.

    Decides report type by user_data["report_type"].
    """

    report_type = _safe_report_type(user_data)

    if report_type == "assessment":
        return generate_assessment_pdf(user_data, output_path)

    if report_type == "solution":
        return generate_solution_pdf(user_data, output_path)

    return _generate_combined_pdf(user_data, output_path)


def generate_therapy_csv(user_data: Dict[str, Any], output_path: str) -> bool:
    """
    Compatibility CSV function used by current app.py.

    Decides report type by user_data["report_type"].
    """

    report_type = _safe_report_type(user_data)

    if report_type == "assessment":
        return generate_assessment_csv(user_data, output_path)

    if report_type == "solution":
        return generate_solution_csv(user_data, output_path)

    return _generate_combined_csv(user_data, output_path)


# =============================================================================
# COMBINED CSV
# =============================================================================

def _generate_combined_csv(user_data: Dict[str, Any], output_path: str) -> bool:
    """
    Combined CSV containing key assessment + solution fields.
    """

    assessment_tmp = _tmp_path(output_path, "assessment_tmp")
    solution_tmp = _tmp_path(output_path, "solution_tmp")

    try:
        generate_assessment_csv(user_data, assessment_tmp)
        generate_solution_csv(user_data, solution_tmp)

        with open(output_path, "w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)

            writer.writerow(["NeuroSense AI Combined Report"])
            writer.writerow(["Generated At", datetime.datetime.now().isoformat()])
            writer.writerow(["Disclaimer", MAIN_DISCLAIMER])
            writer.writerow([])

            writer.writerow(["===== ASSESSMENT REPORT ====="])

            with open(assessment_tmp, "r", encoding="utf-8") as f:
                reader = csv.reader(f)

                for row in reader:
                    writer.writerow(row)

            writer.writerow([])
            writer.writerow(["===== SOLUTION / WELLNESS PLAN ====="])

            with open(solution_tmp, "r", encoding="utf-8") as f:
                reader = csv.reader(f)

                for row in reader:
                    writer.writerow(row)

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    finally:
        for path in [assessment_tmp, solution_tmp]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except OSError:
                pass


# =============================================================================
# Optional direct test
# =============================================================================

if __name__ == "__main__":
    sample = {
        "name": "Test User",
        "email": "test@example.com",
        "lang": "EN",
        "report_date": datetime.date.today().strftime("%d %B %Y"),
        "report_id": "NS-TEST",
        "emotion_freq": {
            "neutral": 5,
            "sad": 2,
            "happy": 1,
        },
        "mood_timeline": [5, 5, 4, 6, None, 5, 5],
        "daily_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "daily_counts": [2, 4, 1, 6, 0, 3, 2],
        "total_messages": 18,
        "streak": 4,
        "top_emotion": "neutral",
        "total_sessions": 3,
        "avg_mood": 5.0,
        "recent_sessions": [],
        "wellbeing_checkins": [
            {
                "mood": "anxious",
                "stress": 4,
                "social_connection": 2,
                "sleep": "poor",
                "concerns": ["academic_pressure", "loneliness"],
                "emotional_safety": 3,
                "support_available": "maybe",
                "current_thoughts": "I feel overwhelmed with work.",
                "wellbeing_score": 42,
                "risk_level": "medium",
            }
        ],
        "latest_wellbeing_checkin": {
            "mood": "anxious",
            "stress": 4,
            "social_connection": 2,
            "sleep": "poor",
            "concerns": ["academic_pressure", "loneliness"],
            "emotional_safety": 3,
            "support_available": "maybe",
            "current_thoughts": "I feel overwhelmed with work.",
            "wellbeing_score": 42,
            "risk_level": "medium",
        },
        "report_type": "solution",
    }

    generate_therapy_pdf(sample, "test_solution_report.pdf")
    generate_therapy_csv(sample, "test_solution_report.csv")

    sample["report_type"] = "assessment"
    generate_therapy_pdf(sample, "test_assessment_report.pdf")
    generate_therapy_csv(sample, "test_assessment_report.csv")

    print("Reports generated.")