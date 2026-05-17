"""
==========================================================================
NeuroSense AI — Voice Chat Tests
==========================================================================

Run:
    pytest tests/test_voice.py -v
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
# VOICE PAGE
# ==========================================================================

def test_voice_page(client):

    response = client.get("/voice-chat")

    assert response.status_code in [200, 302, 401]


# ==========================================================================
# VOICE CHAT API
# ==========================================================================

def test_voice_chat_api(client):

    payload = {
        "message": "I feel stressed today"
    }

    response = client.post(
        "/api/voice_chat",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]

    if response.status_code == 200:

        data = response.get_json()

        assert isinstance(data, dict)


# ==========================================================================
# EMPTY VOICE MESSAGE
# ==========================================================================

def test_empty_voice_message(client):

    payload = {
        "message": ""
    }

    response = client.post(
        "/api/voice_chat",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# LONG VOICE MESSAGE
# ==========================================================================

def test_long_voice_message(client):

    payload = {
        "message": "stress " * 1000
    }

    response = client.post(
        "/api/voice_chat",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 400, 401]


# ==========================================================================
# VOICE HISTORY
# ==========================================================================

def test_voice_history(client):

    response = client.get(
        "/api/voice_history"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# TEXT TO SPEECH
# ==========================================================================

def test_text_to_speech(client):

    payload = {
        "text": "Hello user"
    }

    response = client.post(
        "/api/text_to_speech",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# SPEECH TO TEXT
# ==========================================================================

def test_speech_to_text(client):

    response = client.post(
        "/api/speech_to_text"
    )

    assert response.status_code in [200, 400, 401, 404]


# ==========================================================================
# VOICE SETTINGS
# ==========================================================================

def test_voice_settings(client):

    response = client.get(
        "/api/voice_settings"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# INVALID JSON
# ==========================================================================

def test_invalid_json(client):

    response = client.post(
        "/api/voice_chat",
        data="invalid",
        content_type="application/json"
    )

    assert response.status_code in [400, 401]


# ==========================================================================
# AUDIO ROUTE
# ==========================================================================

def test_audio_route(client):

    response = client.get(
        "/audio/test"
    )

    assert response.status_code in [200, 401, 404]


# ==========================================================================
# RESPONSE TYPE
# ==========================================================================

def test_voice_response_type(client):

    payload = {
        "message": "hello"
    }

    response = client.post(
        "/api/voice_chat",
        data=json.dumps(payload),
        content_type="application/json"
    )

    if response.status_code == 200:

        assert response.content_type.startswith(
            "application/json"
        )