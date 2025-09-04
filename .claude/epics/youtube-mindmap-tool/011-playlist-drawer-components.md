---
id: 011-playlist-drawer-components
title: Playlist Drawer Components Implementation
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: high
estimated_days: 4
dependencies: [006-react-app-foundation, 002-database-schema-design]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [frontend, react, playlist, drawer, ui]
---

# Playlist Drawer Components Implementation

## Description
Implement the playlist management system with hamburger menu-style drawer navigation, drag-and-drop functionality, video thumbnail display, and YouTube-style information layout similar to YouTube's sidebar.

## Acceptance Criteria
- [ ] Hamburger menu drawer with expandable overlay design
- [ ] Playlist list with system playlists frozen at top ("Uncategorized", "Smart Search Result")
- [ ] User-created playlist management (create, rename, delete)
- [ ] Video thumbnail grid with YouTube-style metadata layout
- [ ] Drag-and-drop functionality for video organization between playlists
- [ ] Green plus indicator during drag-to-playlist operations
- [ ] Video information blocks (thumbnail, title, channel, view count, duration)
- [ ] Playlist content drawer with video selection and playback
- [ ] Responsive design for different screen sizes
- [ ] Smooth animations for drawer open/close and transitions
- [ ] Context menus for playlist and video management actions
- [ ] Search/filter functionality within playlists

## Technical Requirements

### Drawer Component Architecture:
```jsx
<PlaylistDrawer isOpen={isPlaylistDrawerOpen}>
  <DrawerOverlay onClick={closeDrawer} />
  <DrawerContent>
    <PlaylistHeader>
      <CloseButton onClick={closeDrawer} />
      <Title>Playlists</Title>
      <CreatePlaylistButton onClick={showCreateModal} />
    </PlaylistHeader>
    
    <SystemPlaylists>
      <PlaylistItem 
        playlist={uncategorizedPlaylist}
        isSystem={true}
        videoCount={uncategorizedCount}
      />
      <PlaylistItem 
        playlist={smartSearchPlaylist}
        isSystem={true}
        videoCount={searchResultCount}
      />
    </SystemPlaylists>
    
    <UserPlaylists>
      {userPlaylists.map(playlist => (
        <DraggablePlaylistItem
          key={playlist.id}
          playlist={playlist}
          onDrop={handleVideoMove}
          onRename={handlePlaylistRename}
          onDelete={handlePlaylistDelete}
        />
      ))}
    </UserPlaylists>
  </DrawerContent>
</PlaylistDrawer>
```

### Video Thumbnail Component:
```jsx
<VideoCard className="group hover:bg-gray-50 transition-colors">
  <VideoThumbnail
    src={video.thumbnailUrl}
    alt={video.title}
    duration={video.duration}
    className="w-32 h-20 object-cover rounded"
  />
  <VideoMetadata className="flex-1 ml-3">
    <VideoTitle className="font-medium text-sm line-clamp-2">
      {video.title}
    </VideoTitle>
    <ChannelName className="text-xs text-gray-600 mt-1">
      {video.channelName}
    </ChannelName>
    <VideoStats className="text-xs text-gray-500 mt-1">
      {video.viewCount} views • {video.uploadDate}
    </VideoStats>
  </VideoMetadata>
  <VideoActions className="opacity-0 group-hover:opacity-100">
    <MoreOptionsButton onClick={showContextMenu} />
  </VideoActions>
</VideoCard>
```

### Drag and Drop APIs:
```
/**
* Drag and Drop Video Management
* Handle video movement between playlists with visual feedback
* Input Parameters: videoId (string), sourcePlaylist (string), targetPlaylist (string)
* Return Parameters: MoveResult with success status and updated playlists
* URL Address: /api/playlists/move-video
* Request Method: POST
**/

/**
* Playlist CRUD Operations
* Create, read, update, delete operations for user playlists
* Input Parameters: operation (string), playlistData (object)
* Return Parameters: PlaylistResult with updated playlist information
* URL Address: /api/playlists/{operation}
* Request Method: POST/GET/PUT/DELETE
**/

/**
* Video Selection and Playback
* Select video from playlist and load in main player
* Input Parameters: videoId (string), playlistId (string), timestamp (number, optional)
* Return Parameters: SelectionResult with video data and playback status
* URL Address: N/A (Frontend state management)
* Request Method: N/A (Frontend state management)
**/
```

### Drag and Drop Implementation:
```typescript
interface DragState {
  draggedVideo: VideoData | null;
  dragOverPlaylist: string | null;
  showDropIndicator: boolean;
  dropIndicatorPosition: { x: number; y: number };
}

// Drag event handlers
const handleDragStart = (video: VideoData) => {
  setDragState({
    draggedVideo: video,
    dragOverPlaylist: null,
    showDropIndicator: false,
    dropIndicatorPosition: { x: 0, y: 0 }
  });
  document.body.style.cursor = 'grabbing';
};

const handleDragOver = (playlistId: string, event: DragEvent) => {
  event.preventDefault();
  setDragState(prev => ({
    ...prev,
    dragOverPlaylist: playlistId,
    showDropIndicator: true,
    dropIndicatorPosition: { x: event.clientX, y: event.clientY }
  }));
};
```

### System Playlist Rules:
- **Uncategorized**: Cannot be deleted, receives videos when parent playlists are deleted
- **Smart Search Result**: Cannot be deleted, automatically populated by search results
- Both system playlists are always visible at the top of the list

## Definition of Done
- Drawer opens/closes smoothly with proper animations
- Playlist hierarchy is correctly displayed with system playlists at top
- Drag and drop functionality works reliably across all playlists
- Video thumbnails and metadata display correctly with YouTube styling
- Create/rename/delete operations work for user playlists
- Visual feedback (green plus indicator) appears during drag operations
- Context menus provide appropriate actions for videos and playlists
- Responsive design adapts to different screen sizes
- Performance remains smooth with large playlists (100+ videos)