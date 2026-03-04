"""
Unit tests for Video endpoints using mocks.

IMPORTANT: These are UNIT tests, NOT integration tests.
- Services are MOCKED (VideoService / JobService)
- Dependencies are OVERRIDDEN
- Database is NOT used for video operations
- Only verify endpoint logic and service invocation

Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock
from fastapi.testclient import TestClient

from app.main import app
from app.services.dependencies import get_video_service, get_job_service
from app.schemas.video import (
    VideoUploadResponse,
    VideoFromJobResponse,
    VideoURLResponse,
    UserVideoItem,
    UserVideoDetailResponse,
    UserVideosResponse,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_video_service():
    return Mock()


@pytest.fixture
def mock_job_service():
    return Mock()


@pytest.fixture
def override_services(mock_video_service: Mock, mock_job_service: Mock):
    app.dependency_overrides[get_video_service] = lambda: mock_video_service
    app.dependency_overrides[get_job_service] = lambda: mock_job_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_video_upload_response():
    return VideoUploadResponse(
        video_id=uuid4(),
        bucket="videos",
        object_key="uploads/test.mp4",
        filename="test.mp4",
        content_type="video/mp4",
        size_bytes=128,
        user_id=uuid4(),
        storage_path="minio://videos/uploads/test.mp4",
        uploaded_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_video_item_response():
    return UserVideoItem(
        video_id=uuid4(),
        filename="clip.mp4",
        status="AVAILABLE",
        uploaded_at=datetime.now(timezone.utc),
        preview_url="https://example.com/preview",
    )


# ============================================================================
# TEST CLASS: POST /videos/upload
# ============================================================================

@pytest.mark.unit
class TestVideoUploadEndpointUnit:
    """Unit tests for POST /api/v1/videos/upload"""

    def test_upload_calls_service_with_file_and_user(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
        sample_video_upload_response: VideoUploadResponse,
    ):
        # Arrange
        mock_video_service.upload_video_authenticated.return_value = (
            sample_video_upload_response
        )

        # Act
        response = client.post(
            "/api/v1/videos/upload",
            files={"file": ("test.mp4", b"video-bytes", "video/mp4")},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        mock_video_service.upload_video_authenticated.assert_called_once()

        uploaded_file = mock_video_service.upload_video_authenticated.call_args[0][0]
        uploaded_user_id = mock_video_service.upload_video_authenticated.call_args[0][1]
        assert uploaded_file.filename == "test.mp4"
        assert uploaded_user_id == sample_user.id

    def test_upload_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.post(
            "/api/v1/videos/upload",
            files={"file": ("test.mp4", b"video-bytes", "video/mp4")},
        )

        # Assert
        assert response.status_code == 401


# ============================================================================
# TEST CLASS: POST /videos/from-job/{job_id}
# ============================================================================

@pytest.mark.unit
class TestVideoFromJobEndpointUnit:
    """Unit tests for POST /api/v1/videos/from-job/{job_id}"""

    def test_video_from_job_calls_services_with_expected_params(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
        mock_job_service: Mock,
    ):
        # Arrange
        job_id = uuid4()
        fake_job = Mock()
        fake_job.id = job_id
        mock_job_service.get_by_id.return_value = fake_job
        mock_video_service.create_video_from_job.return_value = VideoFromJobResponse(
            video_id=uuid4(),
            bucket="videos",
            object_key="jobs/out.mp4",
            filename="out.mp4",
            user_id=sample_user.id,
            storage_path="minio://videos/jobs/out.mp4",
            uploaded_at=datetime.now(timezone.utc),
        )

        # Act
        response = client.post(f"/api/v1/videos/from-job/{job_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 201
        mock_job_service.get_by_id.assert_called_once_with(job_id)
        mock_video_service.create_video_from_job.assert_called_once_with(
            fake_job, sample_user.id
        )

    def test_video_from_job_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.post(f"/api/v1/videos/from-job/{uuid4()}")

        # Assert
        assert response.status_code == 401


# ============================================================================
# TEST CLASS: GET /videos/{video_id}/url
# ============================================================================

@pytest.mark.unit
class TestVideoUrlEndpointUnit:
    """Unit tests for GET /api/v1/videos/{video_id}/url"""

    def test_get_video_url_calls_service_with_expires_in(
        self,
        client: TestClient,
        override_services,
        mock_video_service: Mock,
    ):
        # Arrange
        video_id = uuid4()
        mock_video_service.get_video_url.return_value = VideoURLResponse(
            video_id=video_id,
            url="https://example.com/download",
            expires_in_seconds=600,
            filename="clip.mp4",
        )

        # Act
        response = client.get(f"/api/v1/videos/{video_id}/url?expires_in=600")

        # Assert
        assert response.status_code == 200
        mock_video_service.get_video_url.assert_called_once_with(video_id, 600)

    def test_get_video_url_invalid_expires_in_returns_422(self, client: TestClient):
        # Act (below minimum of 60)
        response = client.get(f"/api/v1/videos/{uuid4()}/url?expires_in=30")

        # Assert
        assert response.status_code == 422


# ============================================================================
# TEST CLASS: GET /videos/my-videos
# ============================================================================

@pytest.mark.unit
class TestMyVideosEndpointUnit:
    """Unit tests for GET /api/v1/videos/my-videos"""

    def test_get_my_videos_calls_service_with_pagination_and_query(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
        sample_video_item_response: UserVideoItem,
    ):
        # Arrange
        mock_video_service.list_user_videos.return_value = UserVideosResponse(
            total=1,
            limit=10,
            offset=5,
            videos=[sample_video_item_response],
        )

        # Act
        response = client.get(
            "/api/v1/videos/my-videos?limit=10&offset=5&q=clip",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        mock_video_service.list_user_videos.assert_called_once_with(
            sample_user.id, limit=10, offset=5, query="clip"
        )

    def test_get_my_videos_without_auth_returns_401(self, client: TestClient):
        # Act
        response = client.get("/api/v1/videos/my-videos")

        # Assert
        assert response.status_code == 401


# ============================================================================
# TEST CLASS: GET/PATCH/DELETE /videos/{video_id}
# ============================================================================

@pytest.mark.unit
class TestVideoByIdEndpointsUnit:
    """Unit tests for /api/v1/videos/{video_id} endpoints"""

    def test_get_my_video_by_id_calls_service(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
    ):
        # Arrange
        video_id = uuid4()
        mock_video_service.get_user_video.return_value = UserVideoDetailResponse(
            video_id=video_id,
            filename="clip.mp4",
            status="AVAILABLE",
            uploaded_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            storage_path="minio://videos/clip.mp4",
            preview_url="https://example.com/preview",
        )

        # Act
        response = client.get(f"/api/v1/videos/{video_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        mock_video_service.get_user_video.assert_called_once_with(video_id, sample_user.id)

    def test_update_my_video_calls_service_with_body(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
    ):
        # Arrange
        video_id = uuid4()
        mock_video_service.update_user_video.return_value = UserVideoItem(
            video_id=video_id,
            filename="nuevo_nombre.mp4",
            status="AVAILABLE",
            uploaded_at=datetime.now(timezone.utc),
            preview_url="https://example.com/preview",
        )

        # Act
        response = client.patch(
            f"/api/v1/videos/{video_id}",
            json={"filename": "nuevo_nombre"},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        mock_video_service.update_user_video.assert_called_once()
        assert mock_video_service.update_user_video.call_args[0][0] == video_id
        assert mock_video_service.update_user_video.call_args[0][1] == sample_user.id
        assert mock_video_service.update_user_video.call_args[0][2].filename == "nuevo_nombre"

    def test_delete_my_video_calls_service_and_returns_204(
        self,
        client: TestClient,
        sample_user,
        auth_headers,
        override_services,
        mock_video_service: Mock,
    ):
        # Arrange
        video_id = uuid4()

        # Act
        response = client.delete(f"/api/v1/videos/{video_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 204
        mock_video_service.delete_user_video.assert_called_once_with(video_id, sample_user.id)
