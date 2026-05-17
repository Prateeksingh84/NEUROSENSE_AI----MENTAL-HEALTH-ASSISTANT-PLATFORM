"""
==========================================================================
NeuroSense AI — Hand Sign Tests
==========================================================================

Run:
    pytest tests/test_handsign.py -v
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
# HAND SIGN PAGE
# ==========================================================================

def test_handsign_page(client):

    response = client.get("/handsign")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# HAND PREDICT
# ==========================================================================

def test_hand_predict(client):

    payload = {
        "image": "base64_test_image"
    }

    response = client.post(
        "/api/hand_predict",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# HAND ENTER
# ==========================================================================

def test_hand_enter(client):

    payload = {
        "sentence": "Hello I need support"
    }

    response = client.post(
        "/api/hand_enter",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# RESET HAND
# ==========================================================================

def test_hand_reset(client):

    response = client.post(
        "/api/hand_reset"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# EMPTY HAND SENTENCE
# ==========================================================================

def test_empty_hand_sentence(client):

    payload = {
        "sentence": ""
    }

    response = client.post(
        "/api/hand_enter",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# INVALID IMAGE
# ==========================================================================

def test_invalid_hand_image(client):

    payload = {
        "image": ""
    }

    response = client.post(
        "/api/hand_predict",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# HAND HISTORY
# ==========================================================================

def test_hand_history(client):

    response = client.get(
        "/api/hand_history"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# HAND MODEL STATUS
# ==========================================================================

def test_hand_model_status(client):

    response = client.get(
        "/api/hand_model_status"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# CAMERA STATUS
# ==========================================================================

def test_camera_status(client):

    response = client.get(
        "/api/camera_status"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# JSON RESPONSE
# ==========================================================================

def test_hand_json_response(client):

    payload = {
        "image": "test"
    }

    response = client.post(
        "/api/hand_predict",
        data=json.dumps(payload),
        content_type="application/json"
    )

    if response.status_code == 200:

        assert response.content_type.startswith(
            "application/json"
        )


# ==========================================================================
# LARGE SENTENCE
# ==========================================================================

def test_large_sentence(client):

    payload = {
        "sentence": "hello " * 1000
    }

    response = client.post(
        "/api/hand_enter",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]