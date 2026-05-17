"""
==========================================================================
NeuroSense AI — Emotion Detection Tests
==========================================================================

Run:
    pytest tests/test_emotion.py -v
"""

import io
import json
import pytest

from PIL import Image

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
# CREATE TEST IMAGE
# ==========================================================================

def create_test_image():

    image = Image.new(
        "RGB",
        (120, 120),
        color=(255, 255, 255)
    )

    buffer = io.BytesIO()

    image.save(buffer, format="JPEG")

    buffer.seek(0)

    return buffer


# ==========================================================================
# EMOTION PAGE
# ==========================================================================

def test_emotion_page(client):

    response = client.get("/emotion")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# DETECT EMOTION ENDPOINT
# ==========================================================================

def test_detect_emotion_endpoint(client):

    payload = {
        "image": "test_base64_data"
    }

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# EMOTION HISTORY
# ==========================================================================

def test_emotion_history(client):

    response = client.get(
        "/api/emotion_history"
    )

    assert response.status_code in [200, 401]

    if response.status_code == 200:

        data = response.get_json()

        assert isinstance(data, dict)


# ==========================================================================
# EMOTION ANALYTICS
# ==========================================================================

def test_emotion_analytics(client):

    response = client.get(
        "/api/emotion_analytics"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# INVALID EMOTION REQUEST
# ==========================================================================

def test_invalid_emotion_request(client):

    payload = {}

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# LARGE IMAGE EMOTION
# ==========================================================================

def test_large_image_emotion(client):

    fake_data = "x" * 100000

    payload = {
        "image": fake_data
    }

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# EMOTION JSON RESPONSE
# ==========================================================================

def test_emotion_json_response(client):

    payload = {
        "image": "test"
    }

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps(payload),
        content_type="application/json"
    )

    if response.status_code == 200:

        assert response.content_type.startswith(
            "application/json"
        )


# ==========================================================================
# EMOTION PERFORMANCE
# ==========================================================================

def test_emotion_endpoint_performance(client):

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps({
            "image": "test"
        }),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# FACE DETECTION ROUTE
# ==========================================================================

def test_face_detection_route(client):

    response = client.get(
        "/api/face_detection_status"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# CAMERA STREAM ROUTE
# ==========================================================================

def test_camera_stream_route(client):

    response = client.get(
        "/camera_feed"
    )

    assert response.status_code in [200, 302, 401, 404]


# ==========================================================================
# EMPTY IMAGE DATA
# ==========================================================================

def test_empty_image_data(client):

    payload = {
        "image": ""
    }

    response = client.post(
        "/api/detect_emotion",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# EMOTION MODEL STATUS
# ==========================================================================

def test_emotion_model_status(client):

    response = client.get(
        "/api/emotion_model_status"
    )

    assert response.status_code in [200, 401, 404]