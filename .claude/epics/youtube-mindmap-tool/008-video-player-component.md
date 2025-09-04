---
id: 008-video-player-component
title: Video Player Component with YouTube Integration
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: medium
estimated_days: 3
dependencies: [006-react-app-foundation, 003-youtube-api-integration]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [frontend, react, video, youtube, player]
---

# Video Player Component with YouTube Integration

## Description
Implement the video player component using YouTube's embedded player API with programmatic control for timestamp navigation, playback synchronization with mind map nodes, and responsive design for the split-screen layout.

## Acceptance Criteria
- [ ] YouTube IFrame Player API integration
- [ ] Programmatic timestamp navigation (seekTo functionality)
- [ ] Play/pause control from mind map interactions
- [ ] Player state synchronization with application state
- [ ] Responsive player sizing within split-screen layout
- [ ] Video loading and error state handling
- [ ] Player controls customization for optimal UX
- [ ] Fullscreen mode support with exit handling
- [ ] Video quality selection and auto-adjustment
- [ ] Progress tracking and current time display
- [ ] Mute/unmute functionality
- [ ] Volume control integration

## Technical Requirements

### Video Player Component Structure:
```jsx
<VideoPlayerSection className="flex-shrink-0" width={splitPaneSize}>
  <div className="relative w-full h-full bg-black">
    <YouTubePlayer
      videoId={currentVideo?.youtubeId}
      onReady={handlePlayerReady}
      onStateChange={handleStateChange}
      onProgress={handleProgress}
      playerVars={{
        autoplay: 0,
        controls: 1,
        disablekb: 0,
        enablejsapi: 1,
        modestbranding: 1,
        rel: 0
      }}
    />
    {isLoading && <LoadingOverlay />}
    {error && <ErrorOverlay message={error} />}
  </div>
</VideoPlayerSection>
```

### Player Control APIs:
```
/**
* YouTube Player Controller
* Control YouTube player programmatically for timestamp navigation
* Input Parameters: action (string), timestamp (number), videoId (string)
* Return Parameters: PlayerState object with current status
* URL Address: N/A (Frontend component with YouTube API)
* Request Method: N/A (Frontend component)
**/

/**
* Video Timestamp Navigation
* Navigate to specific timestamp in video from mind map clicks
* Input Parameters: timestamp (number), autoplay (boolean)
* Return Parameters: NavigationResult with success status
* URL Address: N/A (Frontend functionality)
* Request Method: N/A (Frontend functionality)
**/

/**
* Player State Synchronization
* Sync video player state with application state management
* Input Parameters: playerState (object), videoData (object)
* Return Parameters: SyncResult with updated state
* URL Address: N/A (Frontend state management)
* Request Method: N/A (Frontend state management)
**/
```

### Player Event Handling:
- `onReady`: Initialize player controls and state
- `onStateChange`: Track play/pause/buffering states
- `onProgress`: Update current timestamp for mind map sync
- `onError`: Handle video loading and playback errors

### Responsive Design:
- Maintain 16:9 aspect ratio across different container sizes
- Adjust player controls for touch interfaces
- Handle orientation changes on mobile devices

### Integration Points:
- Mind map node clicks trigger `seekTo(timestamp)`
- Current playback time highlights active mind map nodes
- Player state changes update global application state

## Definition of Done
- YouTube video loads and plays correctly in embedded player
- Timestamp navigation works accurately (±1 second precision)
- Player state synchronization maintains consistency
- Responsive design works across all target screen sizes
- Error handling provides clear feedback for failed video loads
- Player controls are accessible via keyboard navigation
- Performance is smooth during frequent timestamp changes
- Integration with mind map component is seamless