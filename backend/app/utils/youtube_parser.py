"""
YouTube URL parser and validator utility functions
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ParsedYouTubeURL:
    """Parsed YouTube URL result"""
    is_valid: bool
    video_id: Optional[str] = None
    url_type: Optional[str] = None
    original_url: str = ""
    error_message: Optional[str] = None


class YouTubeURLParser:
    """YouTube URL parser and validator"""
    
    # YouTube URL patterns
    URL_PATTERNS = [
        # Standard YouTube URLs
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # YouTube short URLs
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        # Mobile YouTube URLs
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # YouTube embed URLs
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        # YouTube playlist with video
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})&list=',
        # YouTube live URLs
        r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})',
    ]
    
    @classmethod
    def parse_url(cls, url: str) -> ParsedYouTubeURL:
        """
        Parse YouTube URL and extract video ID
        
        Function Description: Parse and validate YouTube URL to extract video ID
        Input Parameters: url (string) - YouTube URL to parse
        Return Parameters: ParsedYouTubeURL object with validation results
        URL Address: N/A (Utility function)
        Request Method: N/A (Utility function)
        """
        if not url or not isinstance(url, str):
            return ParsedYouTubeURL(
                is_valid=False,
                original_url=url or "",
                error_message="URL is required and must be a string"
            )
        
        url = url.strip()
        if not url:
            return ParsedYouTubeURL(
                is_valid=False,
                original_url=url,
                error_message="URL cannot be empty"
            )
        
        # Try each pattern
        for i, pattern in enumerate(cls.URL_PATTERNS):
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                
                # Validate video ID format
                if not cls._is_valid_video_id(video_id):
                    return ParsedYouTubeURL(
                        is_valid=False,
                        video_id=video_id,
                        original_url=url,
                        error_message=f"Invalid video ID format: {video_id}"
                    )
                
                # Determine URL type
                url_type = cls._get_url_type(i, url)
                
                return ParsedYouTubeURL(
                    is_valid=True,
                    video_id=video_id,
                    url_type=url_type,
                    original_url=url
                )
        
        return ParsedYouTubeURL(
            is_valid=False,
            original_url=url,
            error_message="Not a valid YouTube URL"
        )
    
    @classmethod
    def _is_valid_video_id(cls, video_id: str) -> bool:
        """Validate YouTube video ID format"""
        if not video_id or len(video_id) != 11:
            return False
        
        # YouTube video IDs are 11 characters long and contain only alphanumeric, underscore, and hyphen
        return re.match(r'^[a-zA-Z0-9_-]{11}$', video_id) is not None
    
    @classmethod
    def _get_url_type(cls, pattern_index: int, url: str) -> str:
        """Determine URL type based on pattern index and URL structure"""
        url_types = {
            0: "watch",
            1: "short",
            2: "mobile",
            3: "embed",
            4: "playlist",
            5: "live"
        }
        return url_types.get(pattern_index, "unknown")
    
    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """
        Quick method to extract video ID from URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID if valid, None otherwise
        """
        result = cls.parse_url(url)
        return result.video_id if result.is_valid else None
    
    @classmethod
    def is_valid_youtube_url(cls, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        return cls.parse_url(url).is_valid
    
    @classmethod
    def get_canonical_url(cls, video_id: str) -> str:
        """
        Generate canonical YouTube URL from video ID
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Canonical YouTube watch URL
        """
        if not cls._is_valid_video_id(video_id):
            raise ValueError(f"Invalid video ID: {video_id}")
        
        return f"https://www.youtube.com/watch?v={video_id}"
    
    @classmethod
    def get_thumbnail_url(cls, video_id: str, quality: str = "maxresdefault") -> str:
        """
        Generate YouTube thumbnail URL from video ID
        
        Args:
            video_id: YouTube video ID
            quality: Thumbnail quality (maxresdefault, hqdefault, mqdefault, default)
            
        Returns:
            YouTube thumbnail URL
        """
        if not cls._is_valid_video_id(video_id):
            raise ValueError(f"Invalid video ID: {video_id}")
        
        valid_qualities = ["maxresdefault", "hqdefault", "mqdefault", "default"]
        if quality not in valid_qualities:
            quality = "maxresdefault"
        
        return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


def parse_youtube_url(url: str) -> ParsedYouTubeURL:
    """
    Convenience function to parse YouTube URL
    
    Function Description: Parse YouTube URL and return validation results
    Input Parameters: url (string) - YouTube URL to parse
    Return Parameters: ParsedYouTubeURL object
    URL Address: N/A (Utility function)
    Request Method: N/A (Utility function)
    """
    return YouTubeURLParser.parse_url(url)


def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Convenience function to extract video ID from YouTube URL
    
    Function Description: Extract video ID from YouTube URL
    Input Parameters: url (string) - YouTube URL
    Return Parameters: video_id (string) or None if invalid
    URL Address: N/A (Utility function)
    Request Method: N/A (Utility function)
    """
    return YouTubeURLParser.extract_video_id(url)


def is_valid_youtube_url(url: str) -> bool:
    """
    Convenience function to validate YouTube URL
    
    Function Description: Check if URL is a valid YouTube URL
    Input Parameters: url (string) - URL to validate
    Return Parameters: boolean - True if valid
    URL Address: N/A (Utility function)
    Request Method: N/A (Utility function)
    """
    return YouTubeURLParser.is_valid_youtube_url(url)