"""
==========================================================================
NeuroSense AI — Global Pytest Configuration
==========================================================================
"""

import os
import pytest

from app import app


# ==========================================================================
# TEST CONFIG
# ==========================================================================

TEST_ENV = {
    "TESTING": True,
    "WTF_CSRF_ENABLED": False,
    "SECRET_KEY": "test-secret-key",
}


# ==========================================================================
# APPLY TEST CONFIG
# ==========================================================================

for key, value in TEST_ENV.items():
    app.config[key] = value


# ==========================================================================
# CLIENT FIXTURE
# ==========================================================================

@pytest.fixture(scope="function")
def client():

    with app.test_client() as client:
        yield client


# ==========================================================================
# APP FIXTURE
# ==========================================================================

@pytest.fixture(scope="session")
def flask_app():
    return app


# ==========================================================================
# RUN BEFORE EACH TEST
# ==========================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():

    os.environ["FLASK_ENV"] = "testing"

    yield


# ==========================================================================
# SAMPLE USER
# ==========================================================================

@pytest.fixture
def sample_user():

    return {
        "id": "test-user-id",
        "email": "test@neurosense.ai",
        "full_name": "Test User",
        "role": "user"
    }


# ==========================================================================
# SAMPLE ADMIN
# ==========================================================================

@pytest.fixture
def sample_admin():

    return {
        "id": "admin-user-id",
        "email": "admin@neurosense.ai",
        "full_name": "Admin User",
        "role": "admin"
    }


# ==========================================================================
# SAMPLE REPORT
# ==========================================================================

@pytest.fixture
def sample_report():

    return {
        "id": "report-123",
        "title": "Mental Wellness Report",
        "summary": "AI-generated wellness report",
        "mood_score": 8.2,
        "top_emotion": "calm"
    }


# ==========================================================================
# SAMPLE SESSION
# ==========================================================================

@pytest.fixture
def sample_session():

    return {
        "session_id": "session-001",
        "messages": [],
        "emotion": "neutral"
    }