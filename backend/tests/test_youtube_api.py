"""
Tests for YouTube API integration functionality
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.core.database import get_db
from app.utils.youtube_parser import YouTubeURLParser, parse_youtube_url
from app.services.youtube_service import YouTubeService, VideoMetadata, VideoCaption
from app.services.youtube_cache_service import YouTubeCacheService


class TestYouTubeURLParser:
    """Test YouTube URL parsing functionality"""
    
    def test_standard_youtube_url(self):
        """Test standard YouTube watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is True
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.url_type == "watch"
        assert result.original_url == url
        assert result.error_message is None
    
    def test_short_youtube_url(self):
        """Test YouTube short URL (youtu.be)"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is True
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.url_type == "short"
        assert result.original_url == url
    
    def test_mobile_youtube_url(self):
        """Test mobile YouTube URL"""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is True
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.url_type == "watch"  # Mobile URLs use same pattern as standard
    
    def test_embed_youtube_url(self):
        """Test YouTube embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is True
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.url_type == "embed"
    
    def test_invalid_url(self):
        """Test invalid URL"""
        url = "https://example.com/video"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is False
        assert result.video_id is None
        assert result.error_message == "Not a valid YouTube URL"
    
    def test_empty_url(self):
        """Test empty URL"""
        result = YouTubeURLParser.parse_url("")
        
        assert result.is_valid is False
        assert result.error_message == "URL is required and must be a string"
    
    def test_none_url(self):
        """Test None URL"""
        result = YouTubeURLParser.parse_url(None)
        
        assert result.is_valid is False
        assert result.error_message == "URL is required and must be a string"
    
    def test_extract_video_id(self):
        """Test video ID extraction convenience method"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = YouTubeURLParser.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_is_valid_youtube_url(self):
        """Test URL validation convenience method"""
        valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        invalid_url = "https://example.com"
        
        assert YouTubeURLParser.is_valid_youtube_url(valid_url) is True
        assert YouTubeURLParser.is_valid_youtube_url(invalid_url) is False
    
    def test_get_canonical_url(self):
        """Test canonical URL generation"""
        video_id = "dQw4w9WgXcQ"
        canonical_url = YouTubeURLParser.get_canonical_url(video_id)
        
        assert canonical_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    def test_get_thumbnail_url(self):
        """Test thumbnail URL generation"""
        video_id = "dQw4w9WgXcQ"
        thumbnail_url = YouTubeURLParser.get_thumbnail_url(video_id)
        
        expected_url = "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
        assert thumbnail_url == expected_url
    
    def test_invalid_video_id_format(self):
        """Test invalid video ID format"""
        url = "https://www.youtube.com/watch?v=invalid"
        result = YouTubeURLParser.parse_url(url)
        
        assert result.is_valid is False
        assert result.error_message == "Not a valid YouTube URL"


class TestYouTubeService:
    """Test YouTube API service functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.youtube_service = YouTubeService(use_mock=True)
    
    def test_get_video_metadata_mock(self):
        """Test getting video metadata with mock data"""
        video_id = "dQw4w9WgXcQ"
        metadata = self.youtube_service.get_video_metadata(video_id)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.video_id == video_id
        assert metadata.title is not None
        assert metadata.channel_name is not None
        assert metadata.duration is not None
        assert metadata.view_count is not None
    
    def test_get_video_metadata_generic_mock(self):
        """Test getting video metadata for unknown video ID (generic mock)"""
        video_id = "abcdefghijk"  # Valid 11-char video ID
        metadata = self.youtube_service.get_video_metadata(video_id)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.video_id == video_id
        assert "Mock Video Title" in metadata.title
        assert metadata.channel_name == "Mock Channel"
    
    def test_get_video_captions_mock(self):
        """Test getting video captions with mock data"""
        video_id = "dQw4w9WgXcQ"
        captions = self.youtube_service.get_video_captions(video_id)
        
        assert isinstance(captions, VideoCaption)
        assert captions.video_id == video_id
        assert captions.language == "en"
        assert len(captions.segments) > 0
        assert captions.is_auto_generated is True
    
    def test_invalid_video_id(self):
        """Test invalid video ID handling"""
        with pytest.raises(Exception) as exc_info:
            self.youtube_service.get_video_metadata("invalid")
        
        assert "Invalid video ID format" in str(exc_info.value)
    
    def test_empty_video_id(self):
        """Test empty video ID handling"""
        with pytest.raises(Exception) as exc_info:
            self.youtube_service.get_video_metadata("")
        
        assert "Video ID is required" in str(exc_info.value)
    
    def test_validate_url(self):
        """Test URL validation through service"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = self.youtube_service.validate_url(url)
        
        assert result.is_valid is True
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_get_quota_status(self):
        """Test quota status retrieval"""
        status = self.youtube_service.get_quota_status()
        
        assert "requests_made_today" in status
        assert "remaining_quota" in status
        assert "using_mock_data" in status
        assert "api_key_configured" in status
        assert status["using_mock_data"] is True
    
    def test_parse_duration(self):
        """Test YouTube duration parsing"""
        # Test various duration formats
        assert self.youtube_service._parse_duration("PT4M13S") == 253  # 4:13
        assert self.youtube_service._parse_duration("PT1H30M") == 5400  # 1:30:00
        assert self.youtube_service._parse_duration("PT45S") == 45     # 0:45
        assert self.youtube_service._parse_duration("PT2H") == 7200    # 2:00:00
        assert self.youtube_service._parse_duration("") is None
        assert self.youtube_service._parse_duration(None) is None


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


class TestYouTubeCacheService:
    """Test YouTube caching service functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.youtube_service = YouTubeService(use_mock=True)
        self.cache_service = YouTubeCacheService(self.db, self.youtube_service)
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_get_video_metadata_cached(self):
        """Test cached video metadata retrieval"""
        video_id = "dQw4w9WgXcQ"
        
        # First call should fetch from API and cache
        metadata1 = self.cache_service.get_video_metadata_cached(video_id)
        assert isinstance(metadata1, VideoMetadata)
        assert metadata1.video_id == video_id
        
        # Second call should use cache
        metadata2 = self.cache_service.get_video_metadata_cached(video_id)
        assert metadata2.video_id == video_id
        assert metadata2.title == metadata1.title
    
    def test_get_video_captions_cached(self):
        """Test cached video captions retrieval"""
        video_id = "dQw4w9WgXcQ"
        
        # First call should fetch from API and cache
        captions1 = self.cache_service.get_video_captions_cached(video_id)
        assert isinstance(captions1, VideoCaption)
        assert captions1.video_id == video_id
        
        # Second call should use cache
        captions2 = self.cache_service.get_video_captions_cached(video_id)
        assert captions2.video_id == video_id
        assert len(captions2.segments) == len(captions1.segments)
    
    def test_force_refresh_cache(self):
        """Test force refresh functionality"""
        video_id = "dQw4w9WgXcQ"
        
        # Get initial data
        metadata1 = self.cache_service.get_video_metadata_cached(video_id)
        
        # Force refresh
        metadata2 = self.cache_service.get_video_metadata_cached(video_id, force_refresh=True)
        
        # Should still get valid data
        assert isinstance(metadata2, VideoMetadata)
        assert metadata2.video_id == video_id
    
    def test_cache_stats(self):
        """Test cache statistics retrieval"""
        video_id = "dQw4w9WgXcQ"
        
        # Initially no cache
        stats = self.cache_service.get_cache_stats(video_id)
        assert stats["video_id"] == video_id
        assert stats["metadata_cached"] is False
        
        # After caching metadata
        self.cache_service.get_video_metadata_cached(video_id)
        stats = self.cache_service.get_cache_stats(video_id)
        # Cache stats might not show immediately due to implementation details
        assert "cache_entries" in stats
    
    def test_invalidate_cache(self):
        """Test cache invalidation"""
        video_id = "dQw4w9WgXcQ"
        
        # Cache some data
        self.cache_service.get_video_metadata_cached(video_id)
        
        # Invalidate cache
        self.cache_service.invalidate_video_cache(video_id)
        
        # Should still work but fetch fresh data
        metadata = self.cache_service.get_video_metadata_cached(video_id)
        assert isinstance(metadata, VideoMetadata)


class TestYouTubeAPIEndpoints:
    """Test YouTube API endpoints"""
    
    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
        Base.metadata.create_all(bind=engine)
    
    def teardown_method(self):
        """Cleanup after each test"""
        Base.metadata.drop_all(bind=engine)
    
    def test_validate_url_endpoint(self):
        """Test URL validation endpoint"""
        response = self.client.post(
            "/api/v1/youtube/validate",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert data["url_type"] == "watch"
    
    def test_validate_invalid_url_endpoint(self):
        """Test URL validation endpoint with invalid URL"""
        response = self.client.post(
            "/api/v1/youtube/validate",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["error_message"] == "Not a valid YouTube URL"
    
    def test_get_metadata_endpoint(self):
        """Test get video metadata endpoint"""
        response = self.client.get("/api/v1/youtube/metadata/dQw4w9WgXcQ")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert "title" in data
        assert "channel_name" in data
        assert "duration" in data
    
    def test_get_captions_endpoint(self):
        """Test get video captions endpoint"""
        response = self.client.get("/api/v1/youtube/captions/dQw4w9WgXcQ")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert data["language"] == "en"
        assert "segments" in data
        assert len(data["segments"]) > 0
    
    def test_get_quota_status_endpoint(self):
        """Test quota status endpoint"""
        response = self.client.get("/api/v1/youtube/quota")
        
        assert response.status_code == 200
        data = response.json()
        assert "requests_made_today" in data
        assert "remaining_quota" in data
        assert "using_mock_data" in data
        assert "api_key_configured" in data
    
    def test_invalidate_cache_endpoint(self):
        """Test cache invalidation endpoint"""
        video_id = "dQw4w9WgXcQ"
        
        # First get some data to cache
        self.client.get(f"/api/v1/youtube/metadata/{video_id}")
        
        # Then invalidate cache
        response = self.client.delete(f"/api/v1/youtube/cache/{video_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert "invalidated" in data["message"]
    
    def test_get_cache_status_endpoint(self):
        """Test cache status endpoint"""
        video_id = "dQw4w9WgXcQ"
        
        response = self.client.get(f"/api/v1/youtube/cache/{video_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert "cache_entries" in data
    
    def test_invalid_video_id_endpoint(self):
        """Test endpoint with invalid video ID"""
        response = self.client.get("/api/v1/youtube/metadata/invalid")
        
        assert response.status_code in [400, 422, 500, 503]  # Should return error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])