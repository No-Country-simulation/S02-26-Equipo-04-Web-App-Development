"""
Unit tests for Audio endpoints using mocks.

IMPORTANT: These are UNIT tests, NOT integration tests.
- Services are MOCKED (AudioService)
- Dependencies are OVERRIDDEN
- Database is NOT used for audio operations
- Only verify endpoint logic and service invocation

Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock
from fastapi.testclient import TestClient

from app.main import app
from app.services.dependencies import get_audio_service
from app.schemas.audio import (
    AudioUploadResponse,
    AudioURLResponse,
    UserAudioItem,
    UserAudiosResponse,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_audio_service():
    return Mock()


@pytest.fixture
def override_audio_service(mock_audio_service: Mock):
    app.dependency_overrides[get_audio_service] = lambda: mock_audio_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_audio_upload_response():
    return AudioUploadResponse(
        audio_id=uuid4(),
        bucket="audios",
        object_key="uploads/test.mp3",
        filename="test.mp3",
        content_type="audio/mpeg",
        size_bytes=512,
        user_id=uuid4(),
        storage_path="minio://audios/uploads/test.mp3",
        uploaded_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_audio_item_response():
    return UserAudioItem(
        audio_id=uuid4(),
        filename="track.mp3",
        status="uploaded",
        uploaded_at=datetime.now(timezone.utc),
    )


# ============================================================================
# TEST CLASS: POST /audios/audio
# ============================================================================

@pytest.mark.unit
class TestAudioUploadEndpointUnit:
    """Unit tests for POST /api/v1/audios/audio"""

    def test_upload_calls_service_with_file_and_user(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_audio_service,
        mock_audio_service: Mock,
        sample_audio_upload_response: AudioUploadResponse,
    ):
        # Arrange
        mock_audio_service.upload_audio.return_value = sample_audio_upload_response

        # Act
        response = client.post(
            "/api/v1/audios/audio",
            files={"file": ("test.mp3", b"audio-bytes", "audio/mpeg")},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        mock_audio_service.upload_audio.assert_called_once()

        uploaded_file = mock_audio_service.upload_audio.call_args[0][0]
        uploaded_user_id = mock_audio_service.upload_audio.call_args[0][1]
        assert uploaded_file.filename == "test.mp3"
        assert uploaded_user_id == sample_user.id

    def test_upload_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.post(
            "/api/v1/audios/audio",
            files={"file": ("test.mp3", b"audio-bytes", "audio/mpeg")},
        )

        # Assert
        assert response.status_code == 401


# ============================================================================
# TEST CLASS: GET /audios/{audio_id}/url
# ============================================================================

@pytest.mark.unit
class TestAudioUrlEndpointUnit:
    """Unit tests for GET /api/v1/audios/{audio_id}/url"""

    def test_get_audio_url_calls_service_with_expires_in(
        self,
        client: TestClient,
        override_audio_service,
        mock_audio_service: Mock,
    ):
        # Arrange
        audio_id = uuid4()
        mock_audio_service.get_audio_public_url.return_value = AudioURLResponse(
            audio_id=audio_id,
            url="https://example.com/download",
            expires_in_seconds=600,
            filename="track.mp3",
        )

        # Act
        response = client.get(f"/api/v1/audios/{audio_id}/url?expires_in=600")

        # Assert
        assert response.status_code == 200
        mock_audio_service.get_audio_public_url.assert_called_once_with(audio_id, 600)

    def test_get_audio_url_invalid_expires_in_returns_422(self, client: TestClient):
        # Act (below minimum of 60)
        response = client.get(f"/api/v1/audios/{uuid4()}/url?expires_in=30")

        # Assert
        assert response.status_code == 422

    def test_get_audio_url_expires_in_too_large_returns_422(self, client: TestClient):
        # Act (above maximum of 7 * 24 * 3600 = 604800)
        response = client.get(f"/api/v1/audios/{uuid4()}/url?expires_in=700000")

        # Assert
        assert response.status_code == 422


# ============================================================================
# TEST CLASS: GET /audios/my-audios
# ============================================================================

@pytest.mark.unit
class TestMyAudiosEndpointUnit:
    """Unit tests for GET /api/v1/audios/my-audios"""

    def test_get_my_audios_calls_service_with_pagination_and_query(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_audio_service,
        mock_audio_service: Mock,
        sample_audio_item_response: UserAudioItem,
    ):
        # Arrange
        mock_audio_service.list_user_audios.return_value = UserAudiosResponse(
            total=1,
            limit=10,
            offset=5,
            audios=[sample_audio_item_response],
        )

        # Act
        response = client.get(
            "/api/v1/audios/my-audios?limit=10&offset=5&q=track",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        mock_audio_service.list_user_audios.assert_called_once_with(
            sample_user.id, limit=10, offset=5, query="track"
        )

    def test_get_my_audios_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.get("/api/v1/audios/my-audios")

        # Assert
        assert response.status_code == 401

    def test_get_my_audios_default_pagination(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_audio_service,
        mock_audio_service: Mock,
        sample_audio_item_response: UserAudioItem,
    ):
        # Arrange - default limit = 20, offset = 0
        mock_audio_service.list_user_audios.return_value = UserAudiosResponse(
            total=1,
            limit=20,
            offset=0,
            audios=[sample_audio_item_response],
        )

        # Act (no query params)
        response = client.get("/api/v1/audios/my-audios", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        mock_audio_service.list_user_audios.assert_called_once_with(
            sample_user.id, limit=20, offset=0, query=None
        )


# ============================================================================
# TEST CLASS: DELETE /audios/{audio_id}
# ============================================================================

@pytest.mark.unit
class TestAudioDeleteEndpointUnit:
    """Unit tests for DELETE /api/v1/audios/{audio_id}"""

    def test_delete_audio_calls_service_and_returns_204(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_audio_service,
        mock_audio_service: Mock,
    ):
        # Arrange
        audio_id = uuid4()

        # Act
        response = client.delete(f"/api/v1/audios/{audio_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 204
        mock_audio_service.delete_audio.assert_called_once_with(audio_id, sample_user.id)

    def test_delete_audio_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.delete(f"/api/v1/audios/{uuid4()}")

        # Assert
        assert response.status_code == 401
