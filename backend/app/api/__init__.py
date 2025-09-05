"""
API router configuration
"""

from fastapi import APIRouter

# Import sub-routers
from .youtube import router as youtube_router
from .stt import router as stt_router
from .analysis import router as analysis_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(youtube_router)
api_router.include_router(stt_router)
api_router.include_router(analysis_router)

# Health check endpoint
@api_router.get("/health")
async def api_health():
    """API health check"""
    return {"status": "API is healthy", "version": "1.0.0"}

# Placeholder endpoints for future development
@api_router.get("/videos")
async def get_videos():
    """
    Get all videos
    Function Description: Retrieve all processed videos
    Input Parameters: None
    Return Parameters: List of video objects
    URL Address: /api/v1/videos  
    Request Method: GET
    """
    return {"videos": [], "message": "Endpoint ready for implementation"}

@api_router.post("/videos/process")
async def process_video():
    """
    Process YouTube video
    Function Description: Process a YouTube video URL to generate mind map
    Input Parameters: youtube_url (string)
    Return Parameters: processing_id (string), status (string)
    URL Address: /api/v1/videos/process
    Request Method: POST
    """
    return {"message": "Endpoint ready for implementation"}