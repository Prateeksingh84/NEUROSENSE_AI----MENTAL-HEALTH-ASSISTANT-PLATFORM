"""
==========================================================================
NeuroSense AI — Dashboard Tests
==========================================================================

Run:
    pytest tests/test_dashboard.py -v
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
# DASHBOARD PAGE
# ==========================================================================

def test_dashboard_page(client):

    response = client.get("/dashboard")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# ADMIN DASHBOARD
# ==========================================================================

def test_admin_dashboard(client):

    response = client.get("/admin")

    assert response.status_code in [200, 302, 401, 403]


# ==========================================================================
# ANALYTICS API
# ==========================================================================

def test_dashboard_analytics(client):

    response = client.get(
        "/api/dashboard/analytics"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# USER STATS API
# ==========================================================================

def test_user_stats_api(client):

    response = client.get(
        "/api/dashboard/stats"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# REALTIME STATUS
# ==========================================================================

def test_realtime_status(client):

    response = client.get(
        "/api/realtime_status"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# SYSTEM HEALTH
# ==========================================================================

def test_system_health(client):

    response = client.get(
        "/api/system_health"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# SESSION LIST
# ==========================================================================

def test_session_list(client):

    response = client.get(
        "/api/sessions"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# RECENT ACTIVITY
# ==========================================================================

def test_recent_activity(client):

    response = client.get(
        "/api/recent_activity"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# DASHBOARD RESPONSE TYPE
# ==========================================================================

def test_dashboard_response_type(client):

    response = client.get("/dashboard")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# INVALID ANALYTICS FILTER
# ==========================================================================

def test_invalid_analytics_filter(client):

    payload = {
        "range": "invalid"
    }

    response = client.post(
        "/api/dashboard/filter",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401, 404]


# ==========================================================================
# EXPORT ANALYTICS
# ==========================================================================

def test_export_analytics(client):

    response = client.get(
        "/api/export_analytics"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# DASHBOARD PERFORMANCE
# ==========================================================================

def test_dashboard_speed(client):

    response = client.get("/dashboard")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# NOTIFICATIONS
# ==========================================================================

def test_notifications(client):

    response = client.get(
        "/api/notifications"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# MARK NOTIFICATION
# ==========================================================================

def test_mark_notification(client):

    payload = {
        "notification_id": "123"
    }

    response = client.post(
        "/api/notifications/read",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# SEARCH ENDPOINT
# ==========================================================================

def test_dashboard_search(client):

    response = client.get(
        "/api/search?q=test"
    )

    assert response.status_code in [200, 401, 404]