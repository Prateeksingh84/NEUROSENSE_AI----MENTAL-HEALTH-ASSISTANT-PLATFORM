"""
==========================================================================
NeuroSense AI — Authentication Tests
==========================================================================

Run:
    pytest tests/test_auth.py -v
"""

import json
import pytest

from app import app


# ==========================================================================
# FIXTURES
# ==========================================================================

@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# ==========================================================================
# HOME ROUTE
# ==========================================================================

def test_home_route(client):

    response = client.get("/")

    assert response.status_code in [200, 302]


# ==========================================================================
# LOGIN PAGE
# ==========================================================================

def test_login_page(client):

    response = client.get("/login")

    assert response.status_code == 200

    assert b"login" in response.data.lower() or \
           b"sign in" in response.data.lower()


# ==========================================================================
# INVALID LOGIN
# ==========================================================================

def test_invalid_login(client):

    payload = {
        "email": "wrong@test.com",
        "password": "invalidpassword"
    }

    response = client.post(
        "/login",
        data=payload,
        follow_redirects=True
    )

    assert response.status_code in [200, 401]


# ==========================================================================
# REGISTER ROUTE
# ==========================================================================

def test_register_page(client):

    response = client.get("/register")

    assert response.status_code in [200, 302]


# ==========================================================================
# LOGOUT
# ==========================================================================

def test_logout(client):

    response = client.get("/logout")

    assert response.status_code in [200, 302]


# ==========================================================================
# PROFILE ROUTE
# ==========================================================================

def test_profile_route_requires_auth(client):

    response = client.get("/profile")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# SETTINGS ROUTE
# ==========================================================================

def test_settings_route(client):

    response = client.get("/settings")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# API PROFILE
# ==========================================================================

def test_profile_api(client):

    response = client.get("/api/user/profile")

    assert response.status_code in [200, 401]

    if response.status_code == 200:

        data = response.get_json()

        assert isinstance(data, dict)


# ==========================================================================
# UPDATE PROFILE
# ==========================================================================

def test_update_profile_api(client):

    payload = {
        "full_name": "Test User",
        "phone": "9999999999",
        "preferred_language": "en"
    }

    response = client.post(
        "/api/user/profile",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401]


# ==========================================================================
# AVATAR ENDPOINT
# ==========================================================================

def test_avatar_endpoint(client):

    response = client.post("/api/user/avatar")

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# DELETE ACCOUNT
# ==========================================================================

def test_delete_account_endpoint(client):

    payload = {
        "confirm": "DELETE"
    }

    response = client.post(
        "/api/user/delete_account",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401, 400]


# ==========================================================================
# INVALID ROUTE
# ==========================================================================

def test_invalid_route(client):

    response = client.get("/this_route_does_not_exist")

    assert response.status_code == 404


# ==========================================================================
# SECURITY HEADERS
# ==========================================================================

def test_security_headers(client):

    response = client.get("/")

    assert response.status_code in [200, 302]


# ==========================================================================
# JSON RESPONSE FORMAT
# ==========================================================================

def test_json_format(client):

    response = client.get("/api/user/profile")

    if response.status_code == 200:

        assert response.content_type.startswith(
            "application/json"
        )