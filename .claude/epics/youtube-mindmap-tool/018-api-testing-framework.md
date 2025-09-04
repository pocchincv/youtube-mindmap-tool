---
id: 018-api-testing-framework
title: API Testing Framework and Mock Data System
epic: youtube-mindmap-tool
status: backlog
priority: medium
complexity: medium
estimated_days: 3
dependencies: [001-project-setup-and-infrastructure]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [testing, api, mock-data, framework, quality-assurance]
---

# API Testing Framework and Mock Data System

## Description
Implement comprehensive API testing framework with mock data systems for development and testing, following the Epic's requirement for easy switching between mock and real API endpoints, and comprehensive testing with mock data.

## Acceptance Criteria
- [ ] Mock data system with configurable toggle controls
- [ ] Comprehensive mock data sets for different video types and scenarios
- [ ] API testing framework with unit and integration tests
- [ ] Mock YouTube API responses for development
- [ ] Mock STT service responses with various transcript scenarios
- [ ] Mock LLM API responses for content analysis and search
- [ ] Test data generation utilities for different use cases
- [ ] API endpoint testing with various edge cases
- [ ] Performance testing with large datasets
- [ ] Error scenario testing with mock failures
- [ ] Documentation for testing procedures and mock data usage
- [ ] Continuous integration test automation

## Technical Requirements

### Mock Data Control System:
```python
# Environment-based mock control
from enum import Enum
import os
from typing import Dict, Any, Optional

class MockService(Enum):
    YOUTUBE_API = "youtube_api"
    STT_OPENAI = "stt_openai"
    STT_GOOGLE = "stt_google"
    STT_LOCAL = "stt_local"
    LLM_ANALYSIS = "llm_analysis"
    SEARCH_SERVICE = "search_service"

class MockDataManager:
    def __init__(self):
        self.mock_enabled = {}
        self.load_mock_settings()
    
    def load_mock_settings(self):
        """Load mock settings from environment variables"""
        self.mock_enabled = {
            MockService.YOUTUBE_API: os.getenv('MOCK_YOUTUBE_API', 'false').lower() == 'true',
            MockService.STT_OPENAI: os.getenv('MOCK_STT_OPENAI', 'false').lower() == 'true',
            MockService.STT_GOOGLE: os.getenv('MOCK_STT_GOOGLE', 'false').lower() == 'true',
            MockService.STT_LOCAL: os.getenv('MOCK_STT_LOCAL', 'false').lower() == 'true',
            MockService.LLM_ANALYSIS: os.getenv('MOCK_LLM_ANALYSIS', 'false').lower() == 'true',
            MockService.SEARCH_SERVICE: os.getenv('MOCK_SEARCH_SERVICE', 'false').lower() == 'true',
        }
    
    def is_mock_enabled(self, service: MockService) -> bool:
        return self.mock_enabled.get(service, False)
    
    def set_mock_enabled(self, service: MockService, enabled: bool):
        self.mock_enabled[service] = enabled

mock_manager = MockDataManager()
```

### Mock YouTube API Implementation:
```python
class MockYouTubeAPI:
    def __init__(self):
        self.mock_videos = {
            "dQw4w9WgXcQ": {
                "id": "dQw4w9WgXcQ",
                "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
                "channelTitle": "RickAstleyVEVO",
                "duration": "PT3M33S",
                "viewCount": "1234567890",
                "thumbnail": {
                    "high": {
                        "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
                    }
                },
                "captions": [
                    {"start": 0, "duration": 3.5, "text": "We're no strangers to love"},
                    {"start": 3.5, "duration": 3.2, "text": "You know the rules and so do I"},
                    # More caption data...
                ]
            },
            "jNQXAC9IVRw": {  # Educational content
                "id": "jNQXAC9IVRw",
                "title": "Machine Learning Explained",
                "channelTitle": "TechEd",
                "duration": "PT15M42S",
                "viewCount": "987654321",
                "thumbnail": {
                    "high": {
                        "url": "https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg"
                    }
                },
                "captions": [
                    {"start": 0, "duration": 4.1, "text": "Today we're going to learn about machine learning"},
                    {"start": 4.1, "duration": 3.8, "text": "Machine learning is a subset of artificial intelligence"},
                    # More educational content...
                ]
            }
        }
    
    async def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Mock video metadata retrieval"""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        if video_id not in self.mock_videos:
            raise VideoNotFoundError(f"Video {video_id} not found")
        
        return self.mock_videos[video_id]
    
    async def get_video_captions(self, video_id: str) -> List[Dict[str, Any]]:
        """Mock caption retrieval"""
        await asyncio.sleep(0.3)
        
        if video_id not in self.mock_videos:
            raise VideoNotFoundError(f"Video {video_id} not found")
        
        return self.mock_videos[video_id].get("captions", [])
```

### Mock STT Services:
```python
class MockSTTService:
    def __init__(self):
        self.mock_transcripts = {
            "educational": {
                "segments": [
                    {
                        "start": 0.0,
                        "end": 4.1,
                        "text": "Today we're going to learn about machine learning and its applications.",
                        "confidence": 0.95
                    },
                    {
                        "start": 4.1,
                        "end": 8.3,
                        "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                        "confidence": 0.92
                    },
                    # More segments...
                ]
            },
            "entertainment": {
                "segments": [
                    {
                        "start": 0.0,
                        "end": 3.5,
                        "text": "We're no strangers to love, you know the rules and so do I.",
                        "confidence": 0.98
                    },
                    # More segments...
                ]
            }
        }
    
    async def transcribe_audio(self, audio_data: bytes, video_type: str = "educational") -> Dict[str, Any]:
        """Mock transcription with realistic delays"""
        # Simulate processing time based on audio length
        processing_time = len(audio_data) / 1000000  # Simulate based on file size
        await asyncio.sleep(min(processing_time, 10))  # Cap at 10 seconds
        
        return self.mock_transcripts.get(video_type, self.mock_transcripts["educational"])
```

### Testing Framework Setup:
```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_youtube_data():
    """Provide mock YouTube data for tests"""
    return {
        "video_id": "test123",
        "title": "Test Video",
        "channel": "Test Channel",
        "duration": 300,
        "captions": [
            {"start": 0, "duration": 3, "text": "This is a test video"},
            {"start": 3, "duration": 3, "text": "With test captions"}
        ]
    }
```

### API Test Cases:
```python
class TestYouTubeAPI:
    """Test YouTube API integration with mock data"""
    
    @pytest.mark.asyncio
    async def test_video_metadata_extraction(self, client, mock_youtube_data):
        """Test video metadata extraction"""
        # Enable YouTube API mocking
        mock_manager.set_mock_enabled(MockService.YOUTUBE_API, True)
        
        response = client.get(f"/api/youtube/metadata/{mock_youtube_data['video_id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == mock_youtube_data["title"]
        assert data["channelTitle"] == mock_youtube_data["channel"]
    
    @pytest.mark.asyncio
    async def test_invalid_video_id(self, client):
        """Test handling of invalid video IDs"""
        response = client.get("/api/youtube/metadata/invalid_id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
    
    @pytest.mark.asyncio
    async def test_url_validation(self, client):
        """Test YouTube URL validation"""
        test_urls = [
            {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "valid": True},
            {"url": "https://youtu.be/dQw4w9WgXcQ", "valid": True},
            {"url": "https://example.com/invalid", "valid": False},
            {"url": "not_a_url", "valid": False}
        ]
        
        for test_case in test_urls:
            response = client.post("/api/youtube/validate", json={"url": test_case["url"]})
            assert response.status_code == 200
            assert response.json()["is_valid"] == test_case["valid"]

class TestPlaylistAPI:
    """Test playlist management API"""
    
    def test_create_playlist(self, client, db_session):
        """Test playlist creation"""
        playlist_data = {
            "name": "Test Playlist",
            "description": "A test playlist",
            "user_id": "test_user"
        }
        
        response = client.post("/api/playlists/create", json=playlist_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == playlist_data["name"]
        assert data["is_system_playlist"] == False
    
    def test_system_playlist_creation(self, client, db_session):
        """Test that system playlists are created automatically"""
        user_id = "test_user"
        
        response = client.get(f"/api/playlists/user/{user_id}")
        
        assert response.status_code == 200
        playlists = response.json()["playlists"]
        
        system_playlists = [p for p in playlists if p["is_system_playlist"]]
        assert len(system_playlists) == 2
        
        playlist_names = [p["name"] for p in system_playlists]
        assert "Uncategorized" in playlist_names
        assert "Smart Search Result" in playlist_names

class TestProcessingPipeline:
    """Test video processing pipeline with mock services"""
    
    @pytest.mark.asyncio
    async def test_complete_processing_pipeline(self, client, db_session):
        """Test complete video processing from URL to mind map"""
        # Enable all mock services
        for service in MockService:
            mock_manager.set_mock_enabled(service, True)
        
        processing_data = {
            "youtube_url": "https://youtube.com/watch?v=jNQXAC9IVRw",
            "user_id": "test_user",
            "options": {"stt_service": "openai"}
        }
        
        response = client.post("/api/processing/start", json=processing_data)
        
        assert response.status_code == 202
        job = response.json()
        job_id = job["job_id"]
        
        # Wait for processing to complete (with timeout)
        max_wait = 30  # seconds
        waited = 0
        
        while waited < max_wait:
            status_response = client.get(f"/api/processing/status/{job_id}")
            status = status_response.json()
            
            if status["current_stage"] == "completed":
                break
            elif status["current_stage"] == "failed":
                pytest.fail(f"Processing failed: {status['error_message']}")
            
            await asyncio.sleep(1)
            waited += 1
        
        assert status["current_stage"] == "completed"
        assert status["progress_percentage"] == 100
```

### Mock Data Generation Utilities:
```python
class MockDataGenerator:
    """Generate realistic mock data for testing"""
    
    def generate_video_data(self, video_type: str = "educational", duration_minutes: int = 10):
        """Generate mock video data"""
        templates = {
            "educational": {
                "title_templates": [
                    "Introduction to {topic}",
                    "Understanding {topic} Concepts",
                    "Complete Guide to {topic}"
                ],
                "topics": ["Machine Learning", "Data Science", "Programming", "Mathematics"],
                "channels": ["TechEd", "CodeAcademy", "ScienceExplained"]
            },
            "entertainment": {
                "title_templates": [
                    "{artist} - {song} (Official Video)",
                    "Funny {content} Compilation",
                    "Top 10 {category} Videos"
                ],
                "artists": ["Artist One", "Band Two", "Singer Three"],
                "content": ["Cat", "Dog", "Baby", "Fail"],
                "channels": ["MusicVEVO", "FunnyVideos", "Entertainment"]
            }
        }
        
        template = templates.get(video_type, templates["educational"])
        # Generate realistic video data based on templates
        # ... implementation details
    
    def generate_transcript_segments(self, video_type: str, duration_seconds: int):
        """Generate realistic transcript segments"""
        # Implementation for generating transcript data
        pass
    
    def generate_mindmap_structure(self, transcript_data: List[Dict]):
        """Generate realistic mind map structure"""
        # Implementation for generating mind map data
        pass
```

## Definition of Done
- Mock data system allows easy toggling between real and mock APIs
- Comprehensive test coverage for all API endpoints
- Mock data includes various video types and edge cases
- Test framework can run in CI/CD pipeline
- Performance tests validate system behavior under load
- Error scenario tests cover all failure modes
- Documentation explains how to use mock data system
- Integration tests validate end-to-end workflows
- Mock services provide realistic response times and data
- Test utilities make it easy to create new test scenarios