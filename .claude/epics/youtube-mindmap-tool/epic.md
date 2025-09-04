---
id: youtube-mindmap-tool
name: YouTube Video Mind Mapping Tool
prd: 初稿產品需求
status: backlog
progress: 0%
created: 2025-09-04T12:00:00+08:00
updated: 2025-09-04T12:00:00+08:00
priority: high
technology_stack:
  frontend: React + Vite + TypeScript + Tailwind
  backend: Python + FastAPI
  database: TBD
---

# YouTube Video Mind Mapping Tool Epic

## Overview
A comprehensive web application that generates interactive mind maps from YouTube videos, allowing users to navigate content through visual nodes, organize videos into playlists, and perform intelligent searches across video content.

## Core Features

### 1. Video Processing & Mind Map Generation
**Epic Component: Video Analysis Engine**
- Accept YouTube URL input and generate mind maps from video content
- Support both CC subtitle extraction and Speech-to-Text (STT) processing
- Automatically categorize new videos into "Uncategorized" playlist
- Store processed data in both user-side and central database for optimization

**Technical Specifications:**
- STT Services: OpenAI API, Google API, local Whisper, Breeze-ASR-25
- Timestamp extraction for precise video navigation
- Central database caching system to avoid reprocessing

### 2. Interactive Mind Map Navigation
**Epic Component: Mind Map Interface**
- Click-to-play functionality from any mind map node
- Dynamic zoom/expand capabilities for nodes and edges
- Horizontal tree structure (left-to-right growth) with aesthetic design
- Single node highlighting with ancestor node dimming
- Resizable interface with draggable separator between video and mind map areas

**Technical Specifications:**
- Node highlighting logic: one active node, dimmed ancestors to root
- Synchronization between video playback time and active nodes
- Dynamic content adjustment for different screen sizes

### 3. Playlist Management System
**Epic Component: Playlist Organization**
- Hamburger menu-style drawer for playlist navigation (similar to YouTube)
- Drag-and-drop functionality for video organization
- Default playlists: "Uncategorized" and "Smart Search Result" (frozen at top)
- Create/delete playlist functionality
- Video thumbnail display with YouTube-style information layout

**UI Components:**
- Playlist List Drawer: Expandable menu overlay
- Playlist Content Drawer: Video thumbnails with metadata
- Video Information Blocks: Thumbnail, title, channel name, view count
- Delete functionality with logical video movement

### 4. Intelligent Search System
**Epic Component: Smart Search Engine**
- Natural language query processing
- Multi-video segment matching with timestamp precision
- Automatic storage of search results in "Smart Search Result" playlist
- Context-aware video segment highlighting
- RAG (Retrieval-Augmented Generation) operations using LLM APIs

**Technical Specifications:**
- Query matching algorithm for video content
- Multiple result handling with clickable selection
- Integration with mind map highlighting system

### 5. User Interface & Experience
**Epic Component: Main Application Layout**
- Split-screen layout: video player (left) and mind map (right)
- Header navigation with all essential controls
- Modal overlays for settings and search
- Responsive cursor states: pointer → fist → pointer during drag operations

**Header Components (left to right):**
- Hamburger menu icon
- Logo
- YouTube URL input field
- "Start Analysis" button
- Smart search button
- Settings gear button
- Google OAuth button

### 6. Configuration & API Management
**Epic Component: Settings & Authentication**
- API key management interface (OpenAI, Google, etc.)
- Google OAuth integration
- Mock data control system for development
- Settings modal with API configuration

### 7. Data Management & Storage
**Epic Component: Data Architecture**
- Central database for shared video processing results
- User-specific data storage and preferences
- Efficient caching system to minimize reprocessing
- Data persistence across user sessions

**Storage Strategy:**
- Check central database before processing new videos
- Store results in both user and central storage
- Maintain necessary data in central database even after user deletion

## Technical Requirements

### API Design Standards
All mock interfaces must follow this specification:
```
/**
* Interface Name
* Function Description  
* Input Parameters
* Return Parameters
* URL Address
* Request Method
**/
```

### Mock Data Control
- Use mock variables to control development vs production data
- Easy switching between mock and real API endpoints
- Comprehensive testing with mock data

### Deletion Logic
1. **Playlist Deletion**: Move all videos to "Uncategorized"
2. **Video from Playlist**: Move video to "Uncategorized"  
3. **Video from Uncategorized**: Remove from user interface, preserve in central database

### Interaction Patterns
- **Pointer Cursor**: Normal navigation and clicking
- **Fist Cursor**: During drag operations
- **Green Plus Indicator**: Visual feedback during drag-to-playlist operations

## Success Criteria

1. **Core Functionality**: Users can input YouTube URLs and receive interactive mind maps
2. **Navigation**: Seamless jumping between video content via mind map nodes
3. **Organization**: Intuitive playlist management with drag-and-drop
4. **Search**: Natural language search returning relevant video segments
5. **Performance**: Efficient processing with caching to minimize wait times
6. **User Experience**: Intuitive interface matching familiar patterns (YouTube-like)

## Dependencies

### External Services
- YouTube API for video metadata
- STT services (OpenAI/Google/Local)
- LLM APIs for content analysis and search

### Technical Dependencies  
- React ecosystem with TypeScript
- FastAPI backend framework
- Database solution (to be determined)
- Video processing libraries
- Mind map visualization libraries

## Risks & Considerations

1. **API Rate Limits**: Manage usage of external STT and LLM services
2. **Video Processing Time**: Large videos may require significant processing time
3. **Storage Costs**: Balance between user convenience and storage efficiency
4. **Copyright Compliance**: Ensure proper handling of YouTube content per terms of service
5. **Performance**: Mind map rendering performance with large, complex videos

## Next Steps

1. Set up project structure with specified technology stack
2. Implement basic YouTube URL processing and subtitle extraction
3. Create mind map visualization proof of concept
4. Design and implement playlist management system
5. Integrate intelligent search functionality
6. Implement comprehensive API design with mock data
7. User interface polish and responsive design
8. Testing and optimization

This epic provides the foundation for building a comprehensive YouTube video mind mapping tool that transforms passive video consumption into an interactive, organized, and searchable experience.