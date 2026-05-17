import os
import uuid
import tempfile
import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


def generate_pdf_report(
    report_title,
    report_text
):

    temp_dir = tempfile.gettempdir()

    filename = (
        f"report_{uuid.uuid4().hex}.pdf"
    )

    path = os.path.join(temp_dir, filename)

    doc = SimpleDocTemplate(
        path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    style = styles["BodyText"]

    style.textColor = colors.black
    style.fontName = "Helvetica-Bold"
    style.fontSize = 12
    style.leading = 22

    story = []

    title = Paragraph(
        f"<b>{report_title}</b>",
        styles["Title"]
    )

    story.append(title)

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(report_text, style)
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Generated: {datetime.datetime.now()}",
            styles["Italic"]
        )
    )

    doc.build(story)

    return path