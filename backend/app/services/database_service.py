"""
Database service for basic CRUD operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc

from app.models import (
    User, Video, Playlist, PlaylistVideo, MindMapNode, 
    ProcessingCache, SearchHistory, APIConfiguration
)


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # User operations
    def create_user(self, email: str, display_name: str = None, 
                   google_oauth_id: str = None, preferences: Dict[str, Any] = None) -> User:
        """
        Create a new user
        Function Description: Create a new user account
        Input Parameters: email (string), display_name (string, optional), google_oauth_id (string, optional), preferences (dict, optional)
        Return Parameters: User object
        URL Address: N/A (Database operation)
        Request Method: N/A (Database operation)
        """
        user = User(
            email=email,
            display_name=display_name,
            google_oauth_id=google_oauth_id,
            preferences=preferences or {}
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_oauth_id(self, oauth_id: str) -> Optional[User]:
        """Get user by Google OAuth ID"""
        return self.db.query(User).filter(User.google_oauth_id == oauth_id).first()
    
    # Video operations
    def create_video(self, youtube_id: str, title: str, channel_name: str = None,
                    duration: int = None, view_count: int = None, 
                    thumbnail_url: str = None, description: str = None) -> Video:
        """
        Create a new video entry
        Function Description: Create a new video record in database
        Input Parameters: youtube_id (string), title (string), channel_name (string, optional), duration (int, optional), view_count (int, optional), thumbnail_url (string, optional), description (string, optional)
        Return Parameters: Video object
        URL Address: N/A (Database operation)
        Request Method: N/A (Database operation)
        """
        video = Video(
            youtube_id=youtube_id,
            title=title,
            channel_name=channel_name,
            duration=duration,
            view_count=view_count,
            thumbnail_url=thumbnail_url,
            description=description,
            processing_status="pending"
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video
    
    def get_video_by_youtube_id(self, youtube_id: str) -> Optional[Video]:
        """Get video by YouTube ID"""
        return self.db.query(Video).filter(Video.youtube_id == youtube_id).first()
    
    def update_video_processing_status(self, video_id: str, status: str, 
                                     transcript_data: Dict[str, Any] = None) -> Video:
        """Update video processing status"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processing_status = status
            if transcript_data:
                video.transcript_data = transcript_data
            self.db.commit()
            self.db.refresh(video)
        return video
    
    # Playlist operations
    def create_playlist(self, user_id: str, name: str, description: str = None,
                       is_system_playlist: bool = False) -> Playlist:
        """
        Create a new playlist
        Function Description: Create a new playlist for user
        Input Parameters: user_id (string), name (string), description (string, optional), is_system_playlist (bool, optional)
        Return Parameters: Playlist object
        URL Address: N/A (Database operation)
        Request Method: N/A (Database operation)
        """
        playlist = Playlist(
            user_id=user_id,
            name=name,
            description=description,
            is_system_playlist=is_system_playlist
        )
        self.db.add(playlist)
        self.db.commit()
        self.db.refresh(playlist)
        return playlist
    
    def get_user_playlists(self, user_id: str, include_system: bool = True) -> List[Playlist]:
        """Get all playlists for a user"""
        query = self.db.query(Playlist).filter(Playlist.user_id == user_id)
        if not include_system:
            query = query.filter(Playlist.is_system_playlist == False)
        return query.order_by(Playlist.display_order, Playlist.name).all()
    
    def get_system_playlist(self, name: str) -> Optional[Playlist]:
        """Get system playlist by name"""
        return self.db.query(Playlist).filter(
            and_(Playlist.name == name, Playlist.is_system_playlist == True)
        ).first()
    
    # Playlist-Video operations
    def add_video_to_playlist(self, playlist_id: str, video_id: str, position: int = None) -> PlaylistVideo:
        """
        Add video to playlist
        Function Description: Add a video to a specific playlist
        Input Parameters: playlist_id (string), video_id (string), position (int, optional)
        Return Parameters: PlaylistVideo object
        URL Address: N/A (Database operation)
        Request Method: N/A (Database operation)
        """
        if position is None:
            # Get the next position
            max_position = self.db.query(PlaylistVideo).filter(
                PlaylistVideo.playlist_id == playlist_id
            ).count()
            position = max_position
        
        playlist_video = PlaylistVideo(
            playlist_id=playlist_id,
            video_id=video_id,
            position=position
        )
        self.db.add(playlist_video)
        self.db.commit()
        self.db.refresh(playlist_video)
        return playlist_video
    
    def remove_video_from_playlist(self, playlist_id: str, video_id: str) -> bool:
        """Remove video from playlist"""
        playlist_video = self.db.query(PlaylistVideo).filter(
            and_(PlaylistVideo.playlist_id == playlist_id, 
                 PlaylistVideo.video_id == video_id)
        ).first()
        
        if playlist_video:
            self.db.delete(playlist_video)
            self.db.commit()
            return True
        return False
    
    def move_video_to_playlist(self, video_id: str, from_playlist_id: str, 
                              to_playlist_id: str) -> bool:
        """Move video from one playlist to another"""
        # Remove from source playlist
        removed = self.remove_video_from_playlist(from_playlist_id, video_id)
        if removed:
            # Add to destination playlist
            self.add_video_to_playlist(to_playlist_id, video_id)
            return True
        return False
    
    # Mind Map operations
    def create_mindmap_node(self, video_id: str, content: str, 
                           parent_node_id: str = None, timestamp_start: int = None,
                           timestamp_end: int = None, node_type: str = "topic",
                           level: int = 0, display_order: int = 0) -> MindMapNode:
        """Create a mind map node"""
        node = MindMapNode(
            video_id=video_id,
            parent_node_id=parent_node_id,
            content=content,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            node_type=node_type,
            level=level,
            display_order=display_order
        )
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node
    
    def get_video_mindmap_nodes(self, video_id: str) -> List[MindMapNode]:
        """Get all mind map nodes for a video"""
        return self.db.query(MindMapNode).filter(
            MindMapNode.video_id == video_id
        ).order_by(MindMapNode.level, MindMapNode.display_order).all()
    
    # Search History operations
    def create_search_history(self, user_id: str, query: str, results_count: int,
                             search_results: List[Dict[str, Any]] = None,
                             search_duration: int = None) -> SearchHistory:
        """Create search history entry"""
        search_history = SearchHistory(
            user_id=user_id,
            query=query,
            results_count=results_count,
            search_results=search_results or [],
            search_duration=search_duration
        )
        self.db.add(search_history)
        self.db.commit()
        self.db.refresh(search_history)
        return search_history
    
    def get_user_search_history(self, user_id: str, limit: int = 20) -> List[SearchHistory]:
        """Get user search history"""
        return self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.created_at)).limit(limit).all()
    
    # Processing Cache operations
    def set_cache(self, video_id: str, cache_key: str, data_content: Dict[str, Any] = None,
                  text_content: str = None, file_path: str = None, 
                  data_type: str = "json", is_permanent: bool = False) -> ProcessingCache:
        """Set cache entry"""
        # Check if cache entry exists
        cache_entry = self.db.query(ProcessingCache).filter(
            and_(ProcessingCache.video_id == video_id,
                 ProcessingCache.cache_key == cache_key)
        ).first()
        
        if cache_entry:
            # Update existing entry
            cache_entry.data_content = data_content
            cache_entry.text_content = text_content
            cache_entry.file_path = file_path
            cache_entry.data_type = data_type
            cache_entry.is_permanent = is_permanent
        else:
            # Create new entry
            cache_entry = ProcessingCache(
                video_id=video_id,
                cache_key=cache_key,
                data_content=data_content,
                text_content=text_content,
                file_path=file_path,
                data_type=data_type,
                is_permanent=is_permanent
            )
            self.db.add(cache_entry)
        
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry
    
    def get_cache(self, video_id: str, cache_key: str) -> Optional[ProcessingCache]:
        """Get cache entry"""
        cache_entry = self.db.query(ProcessingCache).filter(
            and_(ProcessingCache.video_id == video_id,
                 ProcessingCache.cache_key == cache_key)
        ).first()
        
        if cache_entry and cache_entry.is_valid:
            cache_entry.mark_accessed()
            self.db.commit()
            return cache_entry
        return None
    
    # API Configuration operations  
    def create_api_config(self, user_id: str, service_name: str, service_type: str,
                         api_key_encrypted: str, config_data_encrypted: str = None,
                         public_config: str = None) -> APIConfiguration:
        """Create API configuration"""
        api_config = APIConfiguration(
            user_id=user_id,
            service_name=service_name,
            service_type=service_type,
            api_key_encrypted=api_key_encrypted,
            config_data_encrypted=config_data_encrypted,
            public_config=public_config
        )
        self.db.add(api_config)
        self.db.commit()
        self.db.refresh(api_config)
        return api_config
    
    def get_user_api_configs(self, user_id: str, service_type: str = None) -> List[APIConfiguration]:
        """Get user API configurations"""
        query = self.db.query(APIConfiguration).filter(APIConfiguration.user_id == user_id)
        if service_type:
            query = query.filter(APIConfiguration.service_type == service_type)
        return query.filter(APIConfiguration.is_active == True).all()