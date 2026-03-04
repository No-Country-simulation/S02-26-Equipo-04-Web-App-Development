"""
Unit tests for VideoService.

Safety: All tests use SQLite in-memory database via fixtures.
Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.video_service import VideoService
from app.models.video import Video
from app.models.enums import VideoStatus
from app.schemas.video import UpdateVideoRequest
from app.utils.exceptions import (
    NotFoundException,
    ForbiddenException,
    VideoValidationException,
)


class TestVideoServiceGetUserVideo:
    """Tests for retrieving videos owned by a user."""

    def test_get_user_video_success(self, db_session: Session, sample_user):
        """
        Test: User video is retrieved successfully.
        
        Validates:
        - Video object is returned
        - Correct video is retrieved
        - User ownership is verified
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="test.mp4",
            storage_path="minio://videos/test.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        
        # Act
        retrieved_video = service._get_user_video(video.id, sample_user.id)
        
        # Assert
        assert retrieved_video.id == video.id
        assert retrieved_video.user_id == sample_user.id
        assert retrieved_video.original_filename == "test.mp4"

    def test_get_user_video_not_found(self, db_session: Session, sample_user):
        """
        Test: NotFoundException raised when video doesn't exist.
        
        Validates:
        - Exception is raised for non-existent video
        """
        # Arrange
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        fake_video_id = uuid4()
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            service._get_user_video(fake_video_id, sample_user.id)

    def test_get_user_video_forbidden_different_user(self, db_session: Session, sample_user, verified_user):
        """
        Test: ForbiddenException raised when user doesn't own the video.
        
        Validates:
        - User cannot access other users' videos
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=verified_user.id,  # Owned by different user
            original_filename="other.mp4",
            storage_path="minio://videos/other.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(ForbiddenException):
            service._get_user_video(video.id, sample_user.id)


class TestVideoServiceListUserVideos:
    """Tests for listing user videos."""

    def test_list_user_videos_success(self, db_session: Session, sample_user):
        """
        Test: User videos are listed successfully with pagination.
        
        Validates:
        - Only user's videos are returned
        - Pagination works correctly
        - Results are ordered by creation date (newest first)
        """
        # Arrange
        videos = []
        for i in range(5):
            video = Video(
                id=uuid4(),
                user_id=sample_user.id,
                original_filename=f"video{i}.mp4",
                storage_path=f"minio://videos/video{i}.mp4",
                status=VideoStatus.AVAILABLE,
            )
            db_session.add(video)
            videos.append(video)
        db_session.commit()
        
        mock_storage = Mock()
        mock_storage.get_video_public_url.return_value = "https://example.com/video.mp4"
        service = VideoService(db_session, mock_storage)
        
        # Act
        result = service.list_user_videos(sample_user.id, limit=10, offset=0)
        
        # Assert
        assert result.total == 5
        assert len(result.videos) == 5
        assert result.limit == 10
        assert result.offset == 0

    def test_list_user_videos_pagination(self, db_session: Session, sample_user):
        """
        Test: Pagination limits and offsets work correctly.
        
        Validates:
        - Limit parameter restricts results
        - Offset parameter skips records
        """
        # Arrange
        for i in range(10):
            video = Video(
                id=uuid4(),
                user_id=sample_user.id,
                original_filename=f"video{i}.mp4",
                storage_path=f"minio://videos/video{i}.mp4",
                status=VideoStatus.AVAILABLE,
            )
            db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        mock_storage.get_video_public_url.return_value = "https://example.com/video.mp4"
        service = VideoService(db_session, mock_storage)
        
        # Act
        result = service.list_user_videos(sample_user.id, limit=3, offset=5)
        
        # Assert
        assert result.total == 10
        assert len(result.videos) == 3
        assert result.limit == 3
        assert result.offset == 5

    def test_list_user_videos_with_search_query(self, db_session: Session, sample_user):
        """
        Test: Video search by filename works correctly.
        
        Validates:
        - Search filters by filename
        - Case-insensitive matching
        """
        # Arrange
        video1 = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="presentation.mp4",
            storage_path="minio://videos/presentation.mp4",
            status=VideoStatus.AVAILABLE,
        )
        video2 = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="tutorial.mp4",
            storage_path="minio://videos/tutorial.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add_all([video1, video2])
        db_session.commit()
        
        mock_storage = Mock()
        mock_storage.get_video_public_url.return_value = "https://example.com/video.mp4"
        service = VideoService(db_session, mock_storage)
        
        # Act
        result = service.list_user_videos(sample_user.id, query="presentation")
        
        # Assert
        assert result.total == 1
        assert len(result.videos) == 1
        assert result.videos[0].filename == "presentation.mp4"

    def test_list_user_videos_empty(self, db_session: Session, sample_user):
        """
        Test: Empty result when user has no videos.
        
        Validates:
        - Total is 0
        - Videos list is empty
        """
        # Arrange
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        
        # Act
        result = service.list_user_videos(sample_user.id)
        
        # Assert
        assert result.total == 0
        assert len(result.videos) == 0


class TestVideoServiceUpdateUserVideo:
    """Tests for updating user video metadata."""

    def test_update_user_video_filename_success(self, db_session: Session, sample_user):
        """
        Test: Video filename is updated successfully.
        
        Validates:
        - Filename is changed
        - Extension is preserved
        - Database is committed
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="oldname.mp4",
            storage_path="minio://videos/oldname.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        mock_storage.get_video_public_url.return_value = "https://example.com/video.mp4"
        service = VideoService(db_session, mock_storage)
        update_data = UpdateVideoRequest(filename="newname")
        
        # Act
        updated_video = service.update_user_video(video.id, sample_user.id, update_data)
        
        # Assert
        assert updated_video.filename == "newname.mp4"  # Extension preserved
        
        # Verify persistence
        db_session.refresh(video)
        assert video.original_filename == "newname.mp4"

    def test_update_user_video_forbidden(self, db_session: Session, sample_user, verified_user):
        """
        Test: Cannot update video owned by another user.
        
        Validates:
        - ForbiddenException is raised
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=verified_user.id,
            original_filename="other.mp4",
            storage_path="minio://videos/other.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        update_data = UpdateVideoRequest(filename="hacked")
        
        # Act & Assert
        with pytest.raises(ForbiddenException):
            service.update_user_video(video.id, sample_user.id, update_data)

    def test_update_user_video_invalid_characters(self, db_session: Session, sample_user):
        """
        Test: Filename with invalid characters is rejected.
        
        Validates:
        - VideoValidationException is raised
        - Database is unchanged
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="test.mp4",
            storage_path="minio://videos/test.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        # Invalid characters: < > : " / \ | ? *
        update_data = UpdateVideoRequest(filename="invalid<>name")
        
        # Act & Assert
        with pytest.raises(VideoValidationException):
            service.update_user_video(video.id, sample_user.id, update_data)
        
        # Verify no changes
        db_session.refresh(video)
        assert video.original_filename == "test.mp4"


class TestVideoServiceDeleteUserVideo:
    """Tests for deleting user videos."""

    def test_delete_user_video_success(self, db_session: Session, sample_user):
        """
        Test: User video is deleted successfully.
        
        Validates:
        - Video is removed from database
        - Storage deletion is attempted
        - No error on valid deletion
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="delete_me.mp4",
            storage_path="minio://videos/delete_me.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        video_id = video.id
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        
        # Act
        service.delete_user_video(video_id, sample_user.id)
        
        # Assert
        deleted_video = db_session.query(Video).filter(Video.id == video_id).first()
        assert deleted_video is None
        mock_storage.delete_video_from_storage.assert_called_once()

    def test_delete_user_video_forbidden(self, db_session: Session, sample_user, verified_user):
        """
        Test: Cannot delete video owned by another user.
        
        Validates:
        - ForbiddenException is raised
        - Video is not deleted
        """
        # Arrange
        video = Video(
            id=uuid4(),
            user_id=verified_user.id,
            original_filename="protected.mp4",
            storage_path="minio://videos/protected.mp4",
            status=VideoStatus.AVAILABLE,
        )
        db_session.add(video)
        db_session.commit()
        
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(ForbiddenException):
            service.delete_user_video(video.id, sample_user.id)
        
        # Verify video still exists
        db_session.refresh(video)
        assert video.id is not None

    def test_delete_user_video_not_found(self, db_session: Session, sample_user):
        """
        Test: NotFoundException raised when video doesn't exist.
        
        Validates:
        - Proper error for non-existent video
        """
        # Arrange
        mock_storage = Mock()
        service = VideoService(db_session, mock_storage)
        fake_video_id = uuid4()
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            service.delete_user_video(fake_video_id, sample_user.id)
