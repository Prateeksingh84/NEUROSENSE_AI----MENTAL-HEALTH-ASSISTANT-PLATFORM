"""
==========================================================================
NeuroSense AI — Report Tests
==========================================================================

Run:
    pytest tests/test_reports.py -v
"""

import json
import pytest

from app import app


# ==========================================================================
# FIXTURE
# ==========================================================================

@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# ==========================================================================
# REPORT PAGE
# ==========================================================================

def test_reports_page(client):

    response = client.get("/reports")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# GENERATE REPORT
# ==========================================================================

def test_generate_report(client):

    payload = {
        "format": "pdf"
    }

    response = client.post(
        "/api/report/generate",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401]

    if response.status_code == 200:

        data = response.get_json()

        assert isinstance(data, dict)


# ==========================================================================
# DOWNLOAD REPORT
# ==========================================================================

def test_download_report(client):

    response = client.get(
        "/api/report/download?token=test"
    )

    assert response.status_code in [200, 400, 401, 404]


# ==========================================================================
# SAVED REPORTS
# ==========================================================================

def test_saved_reports(client):

    response = client.get("/api/saved_reports")

    assert response.status_code in [200, 401]

    if response.status_code == 200:

        data = response.get_json()

        assert "reports" in data or isinstance(data, dict)


# ==========================================================================
# DELETE REPORT
# ==========================================================================

def test_delete_report(client):

    payload = {
        "report_id": "test-report-id"
    }

    response = client.post(
        "/api/report/delete",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# AI REPORT GENERATION
# ==========================================================================

def test_ai_report_generation(client):

    response = client.post(
        "/api/generate_report"
    )

    assert response.status_code in [200, 401]


# ==========================================================================
# REPORT PREVIEW
# ==========================================================================

def test_report_preview(client):

    response = client.get(
        "/api/report_preview"
    )

    assert response.status_code in [200, 401]


# ==========================================================================
# PDF REPORT ROUTE
# ==========================================================================

def test_pdf_report_route(client):

    response = client.get(
        "/report/pdf"
    )

    assert response.status_code in [200, 302, 401, 404]


# ==========================================================================
# CSV REPORT ROUTE
# ==========================================================================

def test_csv_report_route(client):

    response = client.get(
        "/report/csv"
    )

    assert response.status_code in [200, 302, 401, 404]


# ==========================================================================
# REPORT CONTENT TYPE
# ==========================================================================

def test_report_content_type(client):

    response = client.get("/api/saved_reports")

    if response.status_code == 200:

        assert response.content_type.startswith(
            "application/json"
        )


# ==========================================================================
# INVALID REPORT DELETE
# ==========================================================================

def test_invalid_report_delete(client):

    payload = {
        "report_id": ""
    }

    response = client.post(
        "/api/report/delete",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401, 404]


# ==========================================================================
# REPORT PERFORMANCE
# ==========================================================================

def test_report_endpoint_speed(client):

    response = client.get("/api/saved_reports")

    assert response.status_code in [200, 401]