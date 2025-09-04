---
id: 016-playlist-management-api
title: Playlist Management API and Backend Logic
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: medium
estimated_days: 3
dependencies: [002-database-schema-design, 012-google-oauth-integration]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [backend, api, playlist, crud, logic]
---

# Playlist Management API and Backend Logic

## Description
Implement comprehensive backend APIs and business logic for playlist management including CRUD operations, video organization, system playlist handling, and deletion logic as specified in the Epic requirements.

## Acceptance Criteria
- [ ] Full CRUD API endpoints for playlist management
- [ ] Video-to-playlist association and movement logic
- [ ] System playlist enforcement ("Uncategorized" and "Smart Search Result")
- [ ] Proper deletion logic implementation (move to Uncategorized, preserve in central DB)
- [ ] Playlist sharing and permission management
- [ ] Bulk operations for video management
- [ ] Playlist statistics and analytics
- [ ] Data validation and constraint enforcement
- [ ] User authorization and access control
- [ ] API rate limiting and abuse prevention
- [ ] Comprehensive error handling and status codes
- [ ] Database transaction management for data consistency

## Technical Requirements

### Playlist Management APIs:
```
/**
* Create User Playlist
* Create a new user-defined playlist with validation
* Input Parameters: playlist_name (string), user_id (string), description (string, optional)
* Return Parameters: PlaylistResult with created playlist data
* URL Address: /api/playlists/create
* Request Method: POST
**/

/**
* Get User Playlists
* Retrieve all playlists for a specific user including system playlists
* Input Parameters: user_id (string), include_system (boolean, default: true)
* Return Parameters: PlaylistCollection with all user playlists
* URL Address: /api/playlists/user/{user_id}
* Request Method: GET
**/

/**
* Update Playlist
* Update playlist properties (name, description, etc.)
* Input Parameters: playlist_id (string), updates (object), user_id (string)
* Return Parameters: UpdateResult with modified playlist data
* URL Address: /api/playlists/{playlist_id}
* Request Method: PUT
**/

/**
* Delete Playlist
* Delete user playlist and move all videos to Uncategorized
* Input Parameters: playlist_id (string), user_id (string)
* Return Parameters: DeleteResult with affected video count
* URL Address: /api/playlists/{playlist_id}
* Request Method: DELETE
**/
```

### Video Management APIs:
```
/**
* Move Video Between Playlists
* Move video from source playlist to target playlist
* Input Parameters: video_id (string), source_playlist_id (string), target_playlist_id (string), user_id (string)
* Return Parameters: MoveResult with updated playlist states
* URL Address: /api/playlists/move-video
* Request Method: POST
**/

/**
* Add Video to Playlist
* Add existing video to specified playlist
* Input Parameters: video_id (string), playlist_id (string), user_id (string)
* Return Parameters: AddResult with updated playlist
* URL Address: /api/playlists/{playlist_id}/videos/{video_id}
* Request Method: POST
**/

/**
* Remove Video from Playlist
* Remove video from playlist (moves to Uncategorized if not system delete)
* Input Parameters: video_id (string), playlist_id (string), user_id (string), permanent_delete (boolean)
* Return Parameters: RemoveResult with removal status
* URL Address: /api/playlists/{playlist_id}/videos/{video_id}
* Request Method: DELETE
**/

/**
* Get Playlist Contents
* Retrieve all videos in a specific playlist with metadata
* Input Parameters: playlist_id (string), user_id (string), page (number), limit (number)
* Return Parameters: PlaylistContents with video list and pagination
* URL Address: /api/playlists/{playlist_id}/contents
* Request Method: GET
**/
```

### Backend Business Logic:
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional

class PlaylistManager:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_playlist(self, user_id: str, name: str, description: str = "") -> Playlist:
        """Create new user playlist with validation"""
        # Validate playlist name uniqueness for user
        existing = self.db.query(Playlist).filter(
            and_(Playlist.user_id == user_id, Playlist.name == name)
        ).first()
        
        if existing:
            raise ValueError(f"Playlist '{name}' already exists")
        
        playlist = Playlist(
            id=generate_uuid(),
            user_id=user_id,
            name=name,
            description=description,
            is_system_playlist=False,
            created_at=datetime.utcnow()
        )
        
        self.db.add(playlist)
        await self.db.commit()
        await self.db.refresh(playlist)
        
        return playlist
    
    async def delete_playlist(self, playlist_id: str, user_id: str) -> DeleteResult:
        """Delete playlist and handle video relocation"""
        playlist = await self.get_playlist_by_id(playlist_id, user_id)
        
        if not playlist:
            raise NotFoundError("Playlist not found")
        
        if playlist.is_system_playlist:
            raise ValidationError("Cannot delete system playlists")
        
        # Get all videos in this playlist
        playlist_videos = self.db.query(PlaylistVideo).filter(
            PlaylistVideo.playlist_id == playlist_id
        ).all()
        
        # Move all videos to Uncategorized playlist
        uncategorized = await self.get_uncategorized_playlist(user_id)
        
        for pv in playlist_videos:
            # Check if video already exists in Uncategorized
            existing = self.db.query(PlaylistVideo).filter(
                and_(
                    PlaylistVideo.playlist_id == uncategorized.id,
                    PlaylistVideo.video_id == pv.video_id
                )
            ).first()
            
            if not existing:
                # Add to Uncategorized
                new_pv = PlaylistVideo(
                    playlist_id=uncategorized.id,
                    video_id=pv.video_id,
                    added_at=datetime.utcnow()
                )
                self.db.add(new_pv)
        
        # Delete playlist-video associations
        self.db.query(PlaylistVideo).filter(
            PlaylistVideo.playlist_id == playlist_id
        ).delete()
        
        # Delete the playlist
        self.db.delete(playlist)
        await self.db.commit()
        
        return DeleteResult(
            success=True,
            videos_moved=len(playlist_videos),
            target_playlist=uncategorized.name
        )
```

### System Playlist Management:
```python
async def ensure_system_playlists(user_id: str) -> Tuple[Playlist, Playlist]:
    """Ensure system playlists exist for user"""
    uncategorized = self.db.query(Playlist).filter(
        and_(
            Playlist.user_id == user_id,
            Playlist.name == "Uncategorized",
            Playlist.is_system_playlist == True
        )
    ).first()
    
    if not uncategorized:
        uncategorized = Playlist(
            id=generate_uuid(),
            user_id=user_id,
            name="Uncategorized",
            is_system_playlist=True,
            created_at=datetime.utcnow()
        )
        self.db.add(uncategorized)
    
    smart_search = self.db.query(Playlist).filter(
        and_(
            Playlist.user_id == user_id,
            Playlist.name == "Smart Search Result",
            Playlist.is_system_playlist == True
        )
    ).first()
    
    if not smart_search:
        smart_search = Playlist(
            id=generate_uuid(),
            user_id=user_id,
            name="Smart Search Result",
            is_system_playlist=True,
            created_at=datetime.utcnow()
        )
        self.db.add(smart_search)
    
    await self.db.commit()
    return uncategorized, smart_search
```

### Video Deletion Logic Implementation:
```python
class VideoDeletionHandler:
    """Handle the three types of video deletion as specified in Epic"""
    
    async def delete_from_playlist(self, video_id: str, playlist_id: str, user_id: str):
        """Move video from playlist to Uncategorized"""
        uncategorized = await self.get_uncategorized_playlist(user_id)
        
        # Remove from source playlist
        self.db.query(PlaylistVideo).filter(
            and_(
                PlaylistVideo.playlist_id == playlist_id,
                PlaylistVideo.video_id == video_id
            )
        ).delete()
        
        # Add to Uncategorized if not already there
        existing = self.db.query(PlaylistVideo).filter(
            and_(
                PlaylistVideo.playlist_id == uncategorized.id,
                PlaylistVideo.video_id == video_id
            )
        ).first()
        
        if not existing:
            new_pv = PlaylistVideo(
                playlist_id=uncategorized.id,
                video_id=video_id,
                added_at=datetime.utcnow()
            )
            self.db.add(new_pv)
        
        await self.db.commit()
    
    async def delete_from_uncategorized(self, video_id: str, user_id: str):
        """Remove from user interface, preserve in central database"""
        # Remove from user's playlists
        user_playlists = self.db.query(Playlist).filter(
            Playlist.user_id == user_id
        ).all()
        
        playlist_ids = [p.id for p in user_playlists]
        
        self.db.query(PlaylistVideo).filter(
            and_(
                PlaylistVideo.playlist_id.in_(playlist_ids),
                PlaylistVideo.video_id == video_id
            )
        ).delete()
        
        # Video remains in central database for other users and caching
        await self.db.commit()
```

### Bulk Operations:
```python
async def bulk_move_videos(self, video_ids: List[str], target_playlist_id: str, user_id: str) -> BulkResult:
    """Move multiple videos to target playlist efficiently"""
    results = []
    
    for video_id in video_ids:
        try:
            # Remove from current playlists (except target)
            current_associations = self.db.query(PlaylistVideo).filter(
                and_(
                    PlaylistVideo.video_id == video_id,
                    PlaylistVideo.playlist_id != target_playlist_id
                )
            ).all()
            
            for assoc in current_associations:
                self.db.delete(assoc)
            
            # Add to target playlist
            new_pv = PlaylistVideo(
                playlist_id=target_playlist_id,
                video_id=video_id,
                added_at=datetime.utcnow()
            )
            self.db.add(new_pv)
            
            results.append({"video_id": video_id, "success": True})
            
        except Exception as e:
            results.append({"video_id": video_id, "success": False, "error": str(e)})
    
    await self.db.commit()
    return BulkResult(results=results)
```

## Definition of Done
- All CRUD operations work correctly with proper validation
- System playlists are automatically created and maintained
- Video movement between playlists follows Epic specifications
- Deletion logic correctly implements the three deletion scenarios
- Bulk operations handle large datasets efficiently
- Database transactions ensure data consistency
- API endpoints have proper error handling and HTTP status codes
- User authorization prevents unauthorized playlist access
- Performance is acceptable for typical usage patterns
- Unit and integration tests cover all business logic scenarios