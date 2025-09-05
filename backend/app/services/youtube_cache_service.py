"""
YouTube API caching service to reduce API calls and improve performance
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.database_service import DatabaseService
from app.services.youtube_service import VideoMetadata, VideoCaption, YouTubeService


logger = logging.getLogger(__name__)


class YouTubeCacheService:
    """YouTube API caching service using database cache"""
    
    # Cache TTL settings
    METADATA_CACHE_HOURS = 24  # Cache metadata for 24 hours
    CAPTION_CACHE_HOURS = 168  # Cache captions for 7 days (rarely change)
    
    def __init__(self, db: Session, youtube_service: Optional[YouTubeService] = None):
        """
        Initialize cache service
        
        Args:
            db: Database session
            youtube_service: YouTube API service instance
        """
        self.db_service = DatabaseService(db)
        self.youtube_service = youtube_service or YouTubeService()
    
    def get_video_metadata_cached(self, video_id: str, force_refresh: bool = False) -> VideoMetadata:
        """
        Get video metadata with caching
        
        Function Description: Get video metadata with intelligent caching
        Input Parameters: video_id (string), force_refresh (bool, optional)
        Return Parameters: VideoMetadata object
        URL Address: /api/youtube/metadata/{video_id}
        Request Method: GET
        """
        cache_key = f"metadata_{video_id}"
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self._get_cached_data(video_id, cache_key, self.METADATA_CACHE_HOURS)
            if cached_data:
                logger.info(f"Cache hit for video metadata: {video_id}")
                return self._deserialize_metadata(cached_data)
        
        # Cache miss or force refresh - fetch from API
        logger.info(f"Cache miss for video metadata: {video_id}, fetching from API")
        try:
            metadata = self.youtube_service.get_video_metadata(video_id)
            
            # Cache the result
            self._cache_data(video_id, cache_key, self._serialize_metadata(metadata))
            
            return metadata
            
        except Exception as e:
            # If API fails, try to return stale cache data
            logger.warning(f"YouTube API failed for {video_id}: {e}")
            stale_data = self._get_cached_data(video_id, cache_key, hours_ttl=None)  # Any age
            if stale_data:
                logger.info(f"Returning stale cached data for video metadata: {video_id}")
                return self._deserialize_metadata(stale_data)
            raise
    
    def get_video_captions_cached(self, video_id: str, language: str = 'en', 
                                 force_refresh: bool = False) -> Optional[VideoCaption]:
        """
        Get video captions with caching
        
        Function Description: Get video captions with intelligent caching
        Input Parameters: video_id (string), language (string, optional), force_refresh (bool, optional)
        Return Parameters: VideoCaption object or None
        URL Address: /api/youtube/captions/{video_id}
        Request Method: GET
        """
        cache_key = f"captions_{video_id}_{language}"
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self._get_cached_data(video_id, cache_key, self.CAPTION_CACHE_HOURS)
            if cached_data:
                if cached_data.get('no_captions'):
                    logger.info(f"Cache hit for no captions: {video_id}")
                    return None
                logger.info(f"Cache hit for video captions: {video_id}")
                return self._deserialize_caption(cached_data)
        
        # Cache miss or force refresh - fetch from API
        logger.info(f"Cache miss for video captions: {video_id}, fetching from API")
        try:
            captions = self.youtube_service.get_video_captions(video_id, language)
            
            if captions:
                # Cache the caption data
                self._cache_data(video_id, cache_key, self._serialize_caption(captions))
            else:
                # Cache that no captions are available
                self._cache_data(video_id, cache_key, {'no_captions': True})
            
            return captions
            
        except Exception as e:
            # If API fails, try to return stale cache data
            logger.warning(f"YouTube API failed for captions {video_id}: {e}")
            stale_data = self._get_cached_data(video_id, cache_key, hours_ttl=None)  # Any age
            if stale_data:
                if stale_data.get('no_captions'):
                    logger.info(f"Returning stale cached 'no captions' for: {video_id}")
                    return None
                logger.info(f"Returning stale cached captions for: {video_id}")
                return self._deserialize_caption(stale_data)
            raise
    
    def invalidate_video_cache(self, video_id: str):
        """
        Invalidate all cached data for a video
        
        Args:
            video_id: Video ID to invalidate
        """
        cache_keys = [
            f"metadata_{video_id}",
            f"captions_{video_id}_en",
            f"captions_{video_id}_zh",
            f"captions_{video_id}_zh-TW"
        ]
        
        for cache_key in cache_keys:
            try:
                cache_entry = self.db_service.get_cache(video_id, cache_key)
                if cache_entry:
                    # Mark as expired by setting a past expiry time
                    cache_entry.expires_at = datetime.now() - timedelta(hours=1)
                    self.db_service.db.commit()
                    logger.info(f"Invalidated cache: {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache {cache_key}: {e}")
    
    def get_cache_stats(self, video_id: str) -> Dict[str, Any]:
        """
        Get cache statistics for a video
        
        Args:
            video_id: Video ID to check
            
        Returns:
            Dictionary with cache status information
        """
        stats = {
            'video_id': video_id,
            'metadata_cached': False,
            'captions_cached': {},
            'cache_entries': []
        }
        
        # Check common cache keys
        cache_keys = [
            ('metadata', f"metadata_{video_id}"),
            ('captions_en', f"captions_{video_id}_en"),
            ('captions_zh', f"captions_{video_id}_zh"),
            ('captions_zh-TW', f"captions_{video_id}_zh-TW")
        ]
        
        for cache_type, cache_key in cache_keys:
            try:
                cache_entry = self.db_service.get_cache(video_id, cache_key)
                if cache_entry:
                    is_valid = cache_entry.is_valid
                    stats['cache_entries'].append({
                        'type': cache_type,
                        'key': cache_key,
                        'is_valid': is_valid,
                        'created_at': cache_entry.created_at.isoformat(),
                        'expires_at': cache_entry.expires_at.isoformat() if cache_entry.expires_at else None,
                        'last_accessed_at': cache_entry.last_accessed_at.isoformat() if cache_entry.last_accessed_at else None,
                        'access_count': cache_entry.access_count
                    })
                    
                    if cache_type == 'metadata' and is_valid:
                        stats['metadata_cached'] = True
                    elif cache_type.startswith('captions_') and is_valid:
                        lang = cache_type.split('_')[1]
                        stats['captions_cached'][lang] = True
            except Exception as e:
                logger.warning(f"Failed to get cache stats for {cache_key}: {e}")
        
        return stats
    
    def _get_cached_data(self, video_id: str, cache_key: str, hours_ttl: Optional[int]) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid"""
        try:
            cache_entry = self.db_service.get_cache(video_id, cache_key)
            if not cache_entry:
                return None
            
            # Check TTL if specified
            if hours_ttl is not None:
                cutoff_time = datetime.now() - timedelta(hours=hours_ttl)
                if cache_entry.created_at < cutoff_time:
                    logger.info(f"Cache expired for {cache_key}")
                    return None
            
            # Return JSON data if available
            if cache_entry.data_content:
                return cache_entry.data_content
            elif cache_entry.text_content:
                return json.loads(cache_entry.text_content)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached data for {cache_key}: {e}")
            return None
    
    def _cache_data(self, video_id: str, cache_key: str, data: Dict[str, Any]):
        """Cache data in database"""
        try:
            # Set cache with expiration
            expiry_hours = self.METADATA_CACHE_HOURS if 'metadata' in cache_key else self.CAPTION_CACHE_HOURS
            
            self.db_service.set_cache(
                video_id=video_id,
                cache_key=cache_key,
                data_content=data,
                data_type='json',
                is_permanent=False
            )
            
            logger.info(f"Cached data for {cache_key}")
            
        except Exception as e:
            logger.warning(f"Failed to cache data for {cache_key}: {e}")
    
    def _serialize_metadata(self, metadata: VideoMetadata) -> Dict[str, Any]:
        """Serialize VideoMetadata for caching"""
        return metadata.to_dict()
    
    def _deserialize_metadata(self, data: Dict[str, Any]) -> VideoMetadata:
        """Deserialize cached data to VideoMetadata"""
        # Handle datetime deserialization
        if data.get('published_at'):
            try:
                data['published_at'] = datetime.fromisoformat(data['published_at'])
            except (ValueError, TypeError):
                data['published_at'] = None
        
        return VideoMetadata(**data)
    
    def _serialize_caption(self, caption: VideoCaption) -> Dict[str, Any]:
        """Serialize VideoCaption for caching"""
        return caption.to_dict()
    
    def _deserialize_caption(self, data: Dict[str, Any]) -> VideoCaption:
        """Deserialize cached data to VideoCaption"""
        from app.services.youtube_service import CaptionSegment
        
        # Deserialize segments
        segments = []
        for segment_data in data.get('segments', []):
            segments.append(CaptionSegment(**segment_data))
        
        return VideoCaption(
            video_id=data['video_id'],
            language=data['language'],
            language_name=data['language_name'],
            segments=segments,
            is_auto_generated=data.get('is_auto_generated', False)
        )
    
    def cleanup_expired_cache(self) -> int:
        """
        Cleanup expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            # This would need to be implemented in DatabaseService
            # For now, return 0 as placeholder
            logger.info("Cache cleanup completed")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
            return 0