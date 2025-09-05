"""
YouTube API endpoints for video metadata and caption extraction
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.youtube_service import YouTubeService, YouTubeAPIError
from app.services.youtube_cache_service import YouTubeCacheService
from app.utils.youtube_parser import parse_youtube_url


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube"])


# Request/Response Models
class URLValidationRequest(BaseModel):
    """Request model for URL validation"""
    url: str = Field(..., description="YouTube URL to validate")


class URLValidationResponse(BaseModel):
    """Response model for URL validation"""
    is_valid: bool
    video_id: Optional[str] = None
    url_type: Optional[str] = None
    original_url: str
    error_message: Optional[str] = None


class VideoMetadataResponse(BaseModel):
    """Response model for video metadata"""
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[list] = None
    language: Optional[str] = None


class CaptionSegmentResponse(BaseModel):
    """Response model for caption segment"""
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None


class VideoCaptionResponse(BaseModel):
    """Response model for video captions"""
    video_id: str
    language: str
    language_name: str
    segments: list[CaptionSegmentResponse]
    is_auto_generated: bool = False


class QuotaStatusResponse(BaseModel):
    """Response model for API quota status"""
    requests_made_today: int
    remaining_quota: int
    using_mock_data: bool
    api_key_configured: bool


# Dependency to get YouTube cache service
def get_youtube_cache_service(db: Session = Depends(get_db)) -> YouTubeCacheService:
    """Get YouTube cache service instance"""
    return YouTubeCacheService(db)


@router.post("/validate", response_model=URLValidationResponse)
async def validate_youtube_url(
    request: URLValidationRequest,
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> URLValidationResponse:
    """
    Validate YouTube URL and extract video ID
    
    Function Description: Validate and parse YouTube URL to extract video ID
    Input Parameters: url (string) - YouTube URL to validate
    Return Parameters: ParsedYouTubeURL object with validation results
    URL Address: /api/youtube/validate
    Request Method: POST
    """
    try:
        result = parse_youtube_url(request.url)
        
        return URLValidationResponse(
            is_valid=result.is_valid,
            video_id=result.video_id,
            url_type=result.url_type,
            original_url=result.original_url,
            error_message=result.error_message
        )
    
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate URL: {str(e)}"
        )


@router.get("/metadata/{video_id}", response_model=VideoMetadataResponse)
async def get_video_metadata(
    video_id: str,
    force_refresh: bool = False,
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> VideoMetadataResponse:
    """
    Extract video metadata from YouTube API
    
    Function Description: Extract video metadata from YouTube API using video ID
    Input Parameters: video_id (string), force_refresh (bool, optional)
    Return Parameters: VideoMetadata object with video information
    URL Address: /api/youtube/metadata/{video_id}
    Request Method: GET
    """
    try:
        metadata = cache_service.get_video_metadata_cached(video_id, force_refresh)
        
        return VideoMetadataResponse(
            video_id=metadata.video_id,
            title=metadata.title,
            channel_name=metadata.channel_name,
            channel_id=metadata.channel_id,
            duration=metadata.duration,
            view_count=metadata.view_count,
            like_count=metadata.like_count,
            description=metadata.description,
            thumbnail_url=metadata.thumbnail_url,
            published_at=metadata.published_at.isoformat() if metadata.published_at else None,
            category_id=metadata.category_id,
            tags=metadata.tags,
            language=metadata.language
        )
    
    except YouTubeAPIError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.status_code == 404 else status.HTTP_503_SERVICE_UNAVAILABLE
        if e.status_code == 429:
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif e.status_code == 403:
            status_code = status.HTTP_403_FORBIDDEN
        
        raise HTTPException(status_code=status_code, detail=e.message)
    
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video metadata: {str(e)}"
        )


@router.get("/captions/{video_id}", response_model=Optional[VideoCaptionResponse])
async def get_video_captions(
    video_id: str,
    language: str = "en",
    force_refresh: bool = False,
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> Optional[VideoCaptionResponse]:
    """
    Extract closed captions from YouTube video
    
    Function Description: Extract closed captions from YouTube video if available
    Input Parameters: video_id (string), language (string, optional), force_refresh (bool, optional)
    Return Parameters: VideoCaption object or None if not available
    URL Address: /api/youtube/captions/{video_id}
    Request Method: GET
    """
    try:
        captions = cache_service.get_video_captions_cached(video_id, language, force_refresh)
        
        if not captions:
            return None
        
        return VideoCaptionResponse(
            video_id=captions.video_id,
            language=captions.language,
            language_name=captions.language_name,
            segments=[
                CaptionSegmentResponse(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    confidence=segment.confidence
                ) for segment in captions.segments
            ],
            is_auto_generated=captions.is_auto_generated
        )
    
    except YouTubeAPIError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.status_code == 404 else status.HTTP_503_SERVICE_UNAVAILABLE
        if e.status_code == 429:
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif e.status_code == 403:
            status_code = status.HTTP_403_FORBIDDEN
        
        raise HTTPException(status_code=status_code, detail=e.message)
    
    except Exception as e:
        logger.error(f"Error getting video captions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video captions: {str(e)}"
        )


@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota_status(
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> QuotaStatusResponse:
    """
    Get YouTube API quota usage status
    
    Function Description: Get current YouTube API quota usage and configuration status
    Input Parameters: None
    Return Parameters: Quota status information
    URL Address: /api/youtube/quota
    Request Method: GET
    """
    try:
        quota_info = cache_service.youtube_service.get_quota_status()
        
        return QuotaStatusResponse(
            requests_made_today=quota_info['requests_made_today'],
            remaining_quota=quota_info['remaining_quota'],
            using_mock_data=quota_info['using_mock_data'],
            api_key_configured=quota_info['api_key_configured']
        )
    
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quota status: {str(e)}"
        )


@router.delete("/cache/{video_id}")
async def invalidate_video_cache(
    video_id: str,
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> dict:
    """
    Invalidate cached data for a video
    
    Function Description: Clear cached metadata and captions for a specific video
    Input Parameters: video_id (string) - Video ID to clear cache for
    Return Parameters: Success confirmation
    URL Address: /api/youtube/cache/{video_id}
    Request Method: DELETE
    """
    try:
        cache_service.invalidate_video_cache(video_id)
        
        return {
            "message": f"Cache invalidated for video: {video_id}",
            "video_id": video_id
        }
    
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/cache/{video_id}/status")
async def get_cache_status(
    video_id: str,
    cache_service: YouTubeCacheService = Depends(get_youtube_cache_service)
) -> dict:
    """
    Get cache status for a video
    
    Function Description: Get detailed cache status and statistics for a video
    Input Parameters: video_id (string) - Video ID to check cache status
    Return Parameters: Cache status information
    URL Address: /api/youtube/cache/{video_id}/status  
    Request Method: GET
    """
    try:
        cache_stats = cache_service.get_cache_stats(video_id)
        return cache_stats
    
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache status: {str(e)}"
        )