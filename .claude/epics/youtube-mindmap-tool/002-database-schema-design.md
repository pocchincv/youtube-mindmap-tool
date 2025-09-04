---
id: 002-database-schema-design
title: Database Schema Design and Models
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: medium
estimated_days: 3
dependencies: [001-project-setup-and-infrastructure]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [database, models, schema]
---

# Database Schema Design and Models

## Description
Design and implement the database schema to support the YouTube mind mapping tool, including tables for videos, playlists, mind map data, user preferences, and central caching system.

## Acceptance Criteria
- [ ] User table with authentication data and preferences
- [ ] Video table with YouTube metadata and processing status
- [ ] Playlist table with user-specific organization
- [ ] PlaylistVideo junction table for many-to-many relationships
- [ ] MindMapNode table for storing mind map structure and content
- [ ] ProcessingCache table for central database optimization
- [ ] SearchHistory table for storing user search queries and results
- [ ] APIConfiguration table for storing user API keys (encrypted)
- [ ] Database migrations system implemented
- [ ] SQLAlchemy models created with proper relationships
- [ ] Database indexing optimized for common queries
- [ ] Data validation constraints implemented

## Technical Requirements

### Core Tables Structure:
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_oauth_id VARCHAR,
    email VARCHAR UNIQUE,
    display_name VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    preferences JSONB
);

-- Videos table  
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    youtube_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    channel_name VARCHAR,
    duration INTEGER,
    view_count INTEGER,
    thumbnail_url VARCHAR,
    processed_at TIMESTAMP,
    transcript_data JSONB,
    processing_status VARCHAR,
    created_at TIMESTAMP
);

-- Playlists table
CREATE TABLE playlists (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR NOT NULL,
    is_system_playlist BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Mind map nodes table
CREATE TABLE mindmap_nodes (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    parent_node_id UUID REFERENCES mindmap_nodes(id),
    content TEXT,
    timestamp_start INTEGER,
    timestamp_end INTEGER,
    node_type VARCHAR,
    position_data JSONB,
    created_at TIMESTAMP
);
```

## API Documentation Standard
```
/**
* Database Models Creation
* Create SQLAlchemy models for all required database tables
* Input Parameters: None (DDL operations)
* Return Parameters: Database tables and relationships
* URL Address: N/A (Database operations)
* Request Method: N/A (Database operations)  
**/
```

## Definition of Done
- All database tables created with proper constraints
- SQLAlchemy models implemented with relationships
- Migration scripts created and tested
- Database seeding script for default playlists created
- Performance indexes added for common query patterns
- Data validation working at database and model levels
- Connection pooling configured for production