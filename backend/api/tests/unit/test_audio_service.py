"""
Unit tests for AudioService.

Safety: All tests use SQLite in-memory database via fixtures.
Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from uuid import uuid4
from io import BytesIO
from sqlalchemy.orm import Session
from unittest.mock import Mock, MagicMock
from fastapi import UploadFile

from app.services.audio_service import AudioService
from app.models.audio import Audio
from app.utils.exceptions import (
    AudioNotFoundException,
    AudioValidationException,
    AudioDBException,
)


class TestAudioServiceUpload:
    """Tests for audio upload functionality."""

    def test_upload_audio_success(self, db_session: Session, sample_user):
        """
        Test: Audio file is uploaded successfully.
        
        Validates:
        - Audio record is created in DB
        - Response contains correct metadata
        """
        # Arrange
        file_content = b"fake audio data"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(file_content)
        mock_file.filename = "test.mp3"
        mock_file.content_type = "audio/mpeg"
        
        mock_storage = Mock()
        mock_storage.upload_fileobj_to_minio.return_value = (
            "minio://audios/test.mp3",
            "audios",
            "test.mp3"
        )
        
        service = AudioService(db_session, mock_storage)
        
        # Act
        response = service.upload_audio(mock_file, sample_user.id)
        
        # Assert
        assert response.audio_id is not None
        assert response.filename == "test.mp3"
        assert response.user_id == sample_user.id
        assert response.size_bytes == len(file_content)
        
        # Verify audio record in DB
        audio = db_session.query(Audio).filter(
            Audio.id == response.audio_id
        ).first()
        assert audio is not None
        assert audio.original_filename == "test.mp3"
        assert audio.user_id == sample_user.id

    def test_upload_audio_invalid_extension(self, db_session: Session, sample_user):
        """
        Test: Upload fails with invalid file extension.
        
        Validates:
        - AudioValidationException raised for unsupported format
        """
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"fake data")
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioValidationException):
            service.upload_audio(mock_file, sample_user.id)

    def test_upload_audio_empty_file(self, db_session: Session, sample_user):
        """
        Test: Upload fails with empty file.
        
        Validates:
        - AudioValidationException raised for empty files
        """
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"")
        mock_file.filename = "empty.mp3"
        mock_file.content_type = "audio/mpeg"
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioValidationException):
            service.upload_audio(mock_file, sample_user.id)

    def test_upload_audio_exceeds_max_size(self, db_session: Session, sample_user):
        """
        Test: Upload fails when file exceeds size limit.
        
        Validates:
        - AudioValidationException raised for oversized files
        """
        # Arrange
        large_content = b"x" * (101 * 1024 * 1024)  # 101 MB
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(large_content)
        mock_file.filename = "large.mp3"
        mock_file.content_type = "audio/mpeg"
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioValidationException):
            service.upload_audio(mock_file, sample_user.id)


class TestAudioServiceGetURL:
    """Tests for getting public download URLs."""

    def test_get_audio_public_url_success(self, db_session: Session, sample_user):
        """
        Test: Public URL is generated successfully.
        
        Validates:
        - URL is returned with correct expiration
        """
        # Arrange
        audio = Audio(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="test.mp3",
            storage_path="minio://audios/test.mp3",
            status="uploaded"
        )
        db_session.add(audio)
        db_session.commit()
        
        mock_storage = Mock()
        mock_storage.get_video_public_url.return_value = "https://presigned-url.com/audio.mp3"
        service = AudioService(db_session, mock_storage)
        
        # Act
        response = service.get_audio_public_url(audio.id, expires_in=7200)
        
        # Assert
        assert response.url == "https://presigned-url.com/audio.mp3"
        assert response.expires_in_seconds == 7200
        assert response.filename == "test.mp3"

    def test_get_audio_public_url_not_found(self, db_session: Session):
        """
        Test: Exception raised when audio doesn't exist.
        
        Validates:
        - AudioNotFoundException for non-existent audio
        """
        # Arrange
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioNotFoundException):
            service.get_audio_public_url(uuid4())


class TestAudioServiceList:
    """Tests for listing user audios."""

    def test_list_user_audios_success(self, db_session: Session, sample_user):
        """
        Test: User audios are listed successfully.
        
        Validates:
        - Only user's audios are returned
        - Pagination works correctly
        """
        # Arrange
        for i in range(5):
            audio = Audio(
                id=uuid4(),
                user_id=sample_user.id,
                original_filename=f"audio{i}.mp3",
                storage_path=f"minio://audios/audio{i}.mp3",
                status="uploaded"
            )
            db_session.add(audio)
        db_session.commit()
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act
        result = service.list_user_audios(sample_user.id, limit=10, offset=0)
        
        # Assert
        assert result.total == 5
        assert len(result.audios) == 5
        assert result.limit == 10
        assert result.offset == 0

    def test_list_user_audios_with_search(self, db_session: Session, sample_user):
        """
        Test: Search filters audios by filename.
        
        Validates:
        - Query parameter filters results correctly
        """
        # Arrange
        audio1 = Audio(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="podcast.mp3",
            storage_path="minio://audios/podcast.mp3",
            status="uploaded"
        )
        audio2 = Audio(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="music.wav",
            storage_path="minio://audios/music.wav",
            status="uploaded"
        )
        db_session.add(audio1)
        db_session.add(audio2)
        db_session.commit()
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act
        result = service.list_user_audios(
            sample_user.id,
            limit=10,
            offset=0,
            query="podcast"
        )
        
        # Assert
        assert result.total == 1
        assert len(result.audios) == 1
        assert result.audios[0].filename == "podcast.mp3"

    def test_list_user_audios_pagination(self, db_session: Session, sample_user):
        """
        Test: Pagination works with limit and offset.
        
        Validates:
        - Limit restricts results
        - Offset skips records
        """
        # Arrange
        for i in range(10):
            audio = Audio(
                id=uuid4(),
                user_id=sample_user.id,
                original_filename=f"audio{i}.mp3",
                storage_path=f"minio://audios/audio{i}.mp3",
                status="uploaded"
            )
            db_session.add(audio)
        db_session.commit()
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act
        result = service.list_user_audios(
            sample_user.id,
            limit=3,
            offset=2
        )
        
        # Assert
        assert result.total == 10
        assert len(result.audios) == 3
        assert result.limit == 3
        assert result.offset == 2


class TestAudioServiceDelete:
    """Tests for audio deletion."""

    def test_delete_audio_success(self, db_session: Session, sample_user):
        """
        Test: Audio is deleted successfully.
        
        Validates:
        - Audio removed from DB
        - Storage service called for cleanup
        """
        # Arrange
        audio = Audio(
            id=uuid4(),
            user_id=sample_user.id,
            original_filename="test.mp3",
            storage_path="minio://audios/test.mp3",
            status="uploaded"
        )
        db_session.add(audio)
        db_session.commit()
        audio_id = audio.id
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act
        service.delete_audio(audio_id, sample_user.id)
        
        # Assert
        deleted_audio = db_session.query(Audio).filter(
            Audio.id == audio_id
        ).first()
        assert deleted_audio is None
        mock_storage.delete_video_from_storage.assert_called_once()

    def test_delete_audio_not_found(self, db_session: Session, sample_user):
        """
        Test: Exception raised when audio doesn't exist.
        
        Validates:
        - AudioNotFoundException for non-existent audio
        """
        # Arrange
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioNotFoundException):
            service.delete_audio(uuid4(), sample_user.id)

    def test_delete_audio_forbidden_different_user(
        self,
        db_session: Session,
        sample_user,
        verified_user
    ):
        """
        Test: User cannot delete another user's audio.
        
        Validates:
        - AudioNotFoundException when user doesn't own audio
        """
        # Arrange
        audio = Audio(
            id=uuid4(),
            user_id=verified_user.id,  # Different user
            original_filename="test.mp3",
            storage_path="minio://audios/test.mp3",
            status="uploaded"
        )
        db_session.add(audio)
        db_session.commit()
        
        mock_storage = Mock()
        service = AudioService(db_session, mock_storage)
        
        # Act & Assert
        with pytest.raises(AudioNotFoundException):
            service.delete_audio(audio.id, sample_user.id)
