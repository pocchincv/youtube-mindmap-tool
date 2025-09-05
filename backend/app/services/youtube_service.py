"""
YouTube API service for video metadata extraction and caption retrieval
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.youtube_parser import YouTubeURLParser, ParsedYouTubeURL
from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """YouTube video metadata structure"""
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    duration: Optional[int] = None  # Duration in seconds
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper datetime serialization"""
        data = asdict(self)
        if self.published_at:
            data['published_at'] = self.published_at.isoformat()
        return data


@dataclass
class CaptionSegment:
    """Caption segment with timing information"""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    text: str
    confidence: Optional[float] = None


@dataclass
class VideoCaption:
    """Video caption data structure"""
    video_id: str
    language: str
    language_name: str
    segments: List[CaptionSegment]
    is_auto_generated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'video_id': self.video_id,
            'language': self.language,
            'language_name': self.language_name,
            'segments': [asdict(segment) for segment in self.segments],
            'is_auto_generated': self.is_auto_generated
        }


class YouTubeAPIError(Exception):
    """YouTube API related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class YouTubeRateLimiter:
    """Simple rate limiter for YouTube API calls"""
    
    def __init__(self, max_requests_per_day: int = 10000):
        self.max_requests_per_day = max_requests_per_day
        self.requests_made = 0
        self.last_reset = datetime.now().date()
    
    def can_make_request(self) -> bool:
        """Check if we can make another request"""
        current_date = datetime.now().date()
        
        # Reset counter if it's a new day
        if current_date > self.last_reset:
            self.requests_made = 0
            self.last_reset = current_date
        
        return self.requests_made < self.max_requests_per_day
    
    def record_request(self):
        """Record that a request was made"""
        self.requests_made += 1
    
    def get_remaining_quota(self) -> int:
        """Get remaining API quota for today"""
        return max(0, self.max_requests_per_day - self.requests_made)


class YouTubeService:
    """YouTube API service for metadata and caption extraction"""
    
    def __init__(self, api_key: Optional[str] = None, use_mock: bool = False):
        """
        Initialize YouTube service
        
        Args:
            api_key: YouTube Data API v3 key
            use_mock: Use mock data for development
        """
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        self.use_mock = use_mock or os.getenv('USE_MOCK_YOUTUBE_API', '').lower() == 'true'
        self.rate_limiter = YouTubeRateLimiter()
        
        if not self.use_mock and not self.api_key:
            logger.warning("YouTube API key not provided, falling back to mock mode")
            self.use_mock = True
        
        # Initialize YouTube API client
        self.youtube = None
        if not self.use_mock:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                logger.info("YouTube API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API client: {e}")
                self.use_mock = True
    
    def get_video_metadata(self, video_id: str) -> VideoMetadata:
        """
        Extract video metadata from YouTube API
        
        Function Description: Extract video metadata from YouTube API using video ID
        Input Parameters: video_id (string) - YouTube video ID
        Return Parameters: VideoMetadata object with video information
        URL Address: /api/youtube/metadata/{video_id}
        Request Method: GET
        """
        if not video_id:
            raise YouTubeAPIError("Video ID is required")
        
        # Validate video ID format
        if not YouTubeURLParser._is_valid_video_id(video_id):
            raise YouTubeAPIError(f"Invalid video ID format: {video_id}")
        
        if self.use_mock:
            return self._get_mock_video_metadata(video_id)
        
        if not self.rate_limiter.can_make_request():
            raise YouTubeAPIError("API rate limit exceeded", 429)
        
        try:
            # Request video details from YouTube API
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            
            self.rate_limiter.record_request()
            response = request.execute()
            
            if not response.get('items'):
                raise YouTubeAPIError(f"Video not found: {video_id}", 404)
            
            video_data = response['items'][0]
            return self._parse_video_metadata(video_data)
            
        except HttpError as e:
            status_code = e.resp.status if e.resp else None
            if status_code == 403:
                raise YouTubeAPIError("API quota exceeded or invalid API key", 403)
            elif status_code == 404:
                raise YouTubeAPIError(f"Video not found: {video_id}", 404)
            else:
                raise YouTubeAPIError(f"YouTube API error: {e}", status_code)
        
        except Exception as e:
            logger.error(f"Unexpected error getting video metadata: {e}")
            raise YouTubeAPIError(f"Failed to get video metadata: {str(e)}")
    
    def get_video_captions(self, video_id: str, language: str = 'en') -> Optional[VideoCaption]:
        """
        Extract closed captions from YouTube video
        
        Function Description: Extract closed captions from YouTube video if available
        Input Parameters: video_id (string), language (string, optional) - Language code
        Return Parameters: VideoCaption object or None if not available
        URL Address: /api/youtube/captions/{video_id}
        Request Method: GET
        """
        if not video_id:
            raise YouTubeAPIError("Video ID is required")
        
        if not YouTubeURLParser._is_valid_video_id(video_id):
            raise YouTubeAPIError(f"Invalid video ID format: {video_id}")
        
        if self.use_mock:
            return self._get_mock_video_captions(video_id, language)
        
        if not self.rate_limiter.can_make_request():
            raise YouTubeAPIError("API rate limit exceeded", 429)
        
        try:
            # List available captions
            captions_request = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            )
            
            self.rate_limiter.record_request()
            captions_response = captions_request.execute()
            
            if not captions_response.get('items'):
                logger.info(f"No captions available for video: {video_id}")
                return None
            
            # Find caption track for requested language
            caption_track = None
            for item in captions_response['items']:
                if item['snippet']['language'] == language:
                    caption_track = item
                    break
            
            # If requested language not found, use first available
            if not caption_track:
                caption_track = captions_response['items'][0]
                language = caption_track['snippet']['language']
            
            # Download caption content
            caption_id = caption_track['id']
            caption_download = self.youtube.captions().download(
                id=caption_id,
                tfmt='srt'  # SubRip Text format
            )
            
            self.rate_limiter.record_request()
            caption_content = caption_download.execute()
            
            # Parse SRT content
            segments = self._parse_srt_content(caption_content.decode('utf-8'))
            
            return VideoCaption(
                video_id=video_id,
                language=language,
                language_name=caption_track['snippet']['name'],
                segments=segments,
                is_auto_generated=caption_track['snippet']['trackKind'] == 'asr'
            )
            
        except HttpError as e:
            status_code = e.resp.status if e.resp else None
            if status_code == 403:
                raise YouTubeAPIError("API quota exceeded or captions not accessible", 403)
            elif status_code == 404:
                logger.info(f"No captions found for video: {video_id}")
                return None
            else:
                raise YouTubeAPIError(f"YouTube API error: {e}", status_code)
        
        except Exception as e:
            logger.error(f"Unexpected error getting video captions: {e}")
            raise YouTubeAPIError(f"Failed to get video captions: {str(e)}")
    
    def validate_url(self, url: str) -> ParsedYouTubeURL:
        """
        Validate YouTube URL and extract video information
        
        Function Description: Validate and parse YouTube URL to extract video ID
        Input Parameters: url (string) - YouTube URL to validate
        Return Parameters: ParsedYouTubeURL object with validation results
        URL Address: /api/youtube/validate
        Request Method: POST
        """
        return YouTubeURLParser.parse_url(url)
    
    def _parse_video_metadata(self, video_data: Dict[str, Any]) -> VideoMetadata:
        """Parse video metadata from YouTube API response"""
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        content_details = video_data.get('contentDetails', {})
        
        # Parse duration from ISO 8601 format (PT4M13S)
        duration_str = content_details.get('duration')
        duration_seconds = self._parse_duration(duration_str) if duration_str else None
        
        # Parse published date
        published_at_str = snippet.get('publishedAt')
        published_at = None
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        return VideoMetadata(
            video_id=video_data['id'],
            title=snippet.get('title', ''),
            channel_name=snippet.get('channelTitle', ''),
            channel_id=snippet.get('channelId', ''),
            duration=duration_seconds,
            view_count=int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else None,
            like_count=int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else None,
            description=snippet.get('description', ''),
            thumbnail_url=snippet.get('thumbnails', {}).get('maxres', {}).get('url') or 
                         snippet.get('thumbnails', {}).get('high', {}).get('url'),
            published_at=published_at,
            category_id=snippet.get('categoryId'),
            tags=snippet.get('tags', []),
            language=snippet.get('defaultAudioLanguage') or snippet.get('defaultLanguage')
        )
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse YouTube duration from ISO 8601 format to seconds"""
        if not duration_str:
            return None
        
        # YouTube duration format: PT4M13S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return None
        
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _parse_srt_content(self, srt_content: str) -> List[CaptionSegment]:
        """Parse SRT subtitle content into caption segments"""
        segments = []
        
        # Split by double newline to get individual subtitle blocks
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # Parse timing line (format: 00:00:12,074 --> 00:00:15,847)
            timing_line = lines[1]
            time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', timing_line)
            
            if not time_match:
                continue
            
            # Convert time to seconds
            start_time = (int(time_match.group(1)) * 3600 + 
                         int(time_match.group(2)) * 60 + 
                         int(time_match.group(3)) + 
                         int(time_match.group(4)) / 1000)
            
            end_time = (int(time_match.group(5)) * 3600 + 
                       int(time_match.group(6)) * 60 + 
                       int(time_match.group(7)) + 
                       int(time_match.group(8)) / 1000)
            
            # Combine text lines
            text = ' '.join(lines[2:])
            
            segments.append(CaptionSegment(
                start_time=start_time,
                end_time=end_time,
                text=text
            ))
        
        return segments
    
    def _get_mock_video_metadata(self, video_id: str) -> VideoMetadata:
        """Generate mock video metadata for development"""
        mock_data = {
            'dQw4w9WgXcQ': VideoMetadata(
                video_id=video_id,
                title='Rick Astley - Never Gonna Give You Up (Official Music Video)',
                channel_name='Rick Astley',
                channel_id='UCuAXFkgsw1L7xaCfnd5JJOw',
                duration=213,
                view_count=1500000000,
                like_count=15000000,
                description='The official video for "Never Gonna Give You Up" by Rick Astley.',
                thumbnail_url=f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                published_at=datetime(2009, 10, 25),
                category_id='10',
                tags=['rick astley', 'never gonna give you up', 'music'],
                language='en'
            ),
            'jNQXAC9IVRw': VideoMetadata(
                video_id=video_id,
                title='Me at the zoo',
                channel_name='jawed',
                channel_id='UC4QobU6STFB0P71PMvOGN5A',
                duration=19,
                view_count=300000000,
                like_count=5000000,
                description='The first video uploaded to YouTube.',
                thumbnail_url=f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                published_at=datetime(2005, 4, 23),
                category_id='22',
                tags=['first video', 'zoo', 'elephants'],
                language='en'
            )
        }
        
        # Return specific mock data if available, otherwise generate generic
        if video_id in mock_data:
            return mock_data[video_id]
        
        return VideoMetadata(
            video_id=video_id,
            title=f'Mock Video Title - {video_id}',
            channel_name='Mock Channel',
            channel_id='UC_MockChannelId',
            duration=300,
            view_count=1000000,
            like_count=50000,
            description='This is a mock video for development testing.',
            thumbnail_url=f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            published_at=datetime.now(),
            category_id='1',
            tags=['mock', 'development'],
            language='en'
        )
    
    def _get_mock_video_captions(self, video_id: str, language: str) -> Optional[VideoCaption]:
        """Generate mock video captions for development"""
        mock_segments = [
            CaptionSegment(0.0, 5.0, "Welcome to this mock video."),
            CaptionSegment(5.0, 10.0, "This is a demonstration of caption functionality."),
            CaptionSegment(10.0, 15.0, "The captions are automatically generated for testing."),
            CaptionSegment(15.0, 20.0, "Thank you for watching!")
        ]
        
        return VideoCaption(
            video_id=video_id,
            language=language,
            language_name='English',
            segments=mock_segments,
            is_auto_generated=True
        )
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current API quota usage status"""
        return {
            'requests_made_today': self.rate_limiter.requests_made,
            'remaining_quota': self.rate_limiter.get_remaining_quota(),
            'using_mock_data': self.use_mock,
            'api_key_configured': bool(self.api_key and not self.use_mock)
        }