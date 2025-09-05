"""
Content Analysis API endpoints for mind map generation
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.content_analysis import (
    ContentAnalysisManager,
    AnalysisConfig,
    ContentType,
    ContentAnalysisError
)
from app.services.stt_services.manager import STTServiceManager
from app.utils.audio_utils import YouTubeAudioExtractor, AudioProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Content Analysis"])


# Request/Response Models
class GenerateMindMapRequest(BaseModel):
    """Request model for mind map generation"""
    video_id: str = Field(..., description="YouTube video ID")
    content_type: Optional[str] = Field(None, description="Content type (educational, tutorial, etc.)")
    max_depth: Optional[int] = Field(4, description="Maximum depth of mind map", ge=1, le=10)
    language: Optional[str] = Field(None, description="Content language")
    use_existing_transcript: bool = Field(True, description="Use existing transcript if available")


class AnalysisConfigRequest(BaseModel):
    """Request model for custom analysis configuration"""
    max_depth: int = Field(4, ge=1, le=10)
    min_segment_duration: float = Field(10.0, ge=1.0, le=600.0)
    max_segment_duration: float = Field(300.0, ge=10.0, le=1800.0)
    content_type: str = Field("educational")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0)
    importance_threshold: float = Field(0.4, ge=0.0, le=1.0)


class TopicExtractionRequest(BaseModel):
    """Request model for topic extraction"""
    content: str = Field(..., description="Text content to analyze")
    max_topics: int = Field(10, description="Maximum number of topics", ge=1, le=50)


class SummarizationRequest(BaseModel):
    """Request model for content summarization"""
    content: str = Field(..., description="Text content to summarize")
    max_length: int = Field(100, description="Maximum summary length", ge=10, le=500)


class MindMapResponse(BaseModel):
    """Response model for mind map structure"""
    video_id: str
    nodes_count: int
    processing_time: float
    confidence_score: float
    content_type: str
    total_duration: float
    nodes: list


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis service status"""
    service_name: str
    using_mock: bool
    analyzer_type: str
    features: Dict[str, bool]
    supported_content_types: list
    version: str


# Dependency to get content analysis manager
def get_analysis_manager() -> ContentAnalysisManager:
    """Get content analysis manager instance"""
    return ContentAnalysisManager()


def get_stt_manager() -> STTServiceManager:
    """Get STT service manager instance"""
    return STTServiceManager()


@router.post("/generate-mindmap", response_model=MindMapResponse)
async def generate_mind_map(
    request: GenerateMindMapRequest,
    background_tasks: BackgroundTasks,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager),
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> MindMapResponse:
    """
    Generate mind map structure from YouTube video
    
    Function Description: Analyze video content and generate hierarchical mind map
    Input Parameters: video_id (string), content_type (string, optional), max_depth (int, optional)
    Return Parameters: MindMapResponse with hierarchical node structure
    URL Address: /api/analysis/generate-mindmap
    Request Method: POST
    """
    try:
        logger.info(f"Generating mind map for video: {request.video_id}")
        
        # Step 1: Get or create transcript
        transcript = None
        
        if request.use_existing_transcript:
            # Try to get existing transcript from STT service
            # This would typically check database for cached results
            logger.info("Checking for existing transcript...")
            
        if not transcript:
            # Extract audio and transcribe
            logger.info("Extracting audio and generating transcript...")
            audio_extractor = YouTubeAudioExtractor()
            
            try:
                audio_info = audio_extractor.extract_audio(request.video_id, format="wav")
                logger.info(f"Audio extracted: {audio_info.duration:.2f}s")
                
                # Transcribe audio
                transcript = stt_manager.transcribe_audio(
                    audio_info=audio_info,
                    language=request.language
                )
                
            finally:
                # Clean up temporary files
                audio_extractor.cleanup_temp_files()
        
        # Step 2: Create analysis configuration
        content_type = ContentType.EDUCATIONAL
        if request.content_type:
            try:
                content_type = ContentType(request.content_type.lower())
            except ValueError:
                logger.warning(f"Invalid content type: {request.content_type}, using default")
        
        config = AnalysisConfig(
            max_depth=request.max_depth,
            content_type=content_type,
            language=request.language or transcript.language or "en"
        )
        
        # Step 3: Generate mind map
        mind_map = analysis_manager.generate_mind_map(transcript, config)
        
        # Step 4: Save to database (in background)
        background_tasks.add_task(analysis_manager.save_mind_map, mind_map)
        
        # Step 5: Return response
        return MindMapResponse(
            video_id=mind_map.video_id,
            nodes_count=len(mind_map.nodes),
            processing_time=mind_map.processing_time,
            confidence_score=mind_map.confidence_score,
            content_type=mind_map.content_type.value,
            total_duration=mind_map.total_duration,
            nodes=[node.__dict__ for node in mind_map.nodes]
        )
        
    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Audio processing failed: {e.message}"
        )
    
    except ContentAnalysisError as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Content analysis failed: {e.message}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during mind map generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mind map generation failed: {str(e)}"
        )


@router.get("/mindmap/{video_id}")
async def get_mind_map(
    video_id: str,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager)
) -> Dict[str, Any]:
    """
    Get existing mind map for video
    
    Function Description: Retrieve stored mind map structure for a video
    Input Parameters: video_id (string)
    Return Parameters: Mind map data with nodes and statistics
    URL Address: /api/analysis/mindmap/{video_id}
    Request Method: GET
    """
    try:
        mind_map = analysis_manager.get_mind_map(video_id)
        
        if not mind_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mind map not found for video: {video_id}"
            )
        
        return mind_map
        
    except Exception as e:
        logger.error(f"Error retrieving mind map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mind map: {str(e)}"
        )


@router.delete("/mindmap/{video_id}")
async def delete_mind_map(
    video_id: str,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager)
) -> Dict[str, Any]:
    """
    Delete mind map for video
    
    Function Description: Remove stored mind map data for a video
    Input Parameters: video_id (string)
    Return Parameters: Deletion status
    URL Address: /api/analysis/mindmap/{video_id}
    Request Method: DELETE
    """
    try:
        success = analysis_manager.delete_mind_map(video_id)
        
        if success:
            return {"success": True, "message": f"Mind map deleted for video: {video_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mind map not found for video: {video_id}"
            )
        
    except Exception as e:
        logger.error(f"Error deleting mind map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete mind map: {str(e)}"
        )


@router.post("/extract-topics")
async def extract_topics(
    request: TopicExtractionRequest,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager)
) -> Dict[str, Any]:
    """
    Extract topics from text content
    
    Function Description: Extract main topics and subtopics from text content
    Input Parameters: content (string), max_topics (number)
    Return Parameters: List of extracted topics with confidence scores
    URL Address: /api/analysis/extract-topics
    Request Method: POST
    """
    try:
        config = AnalysisConfig()
        analyzer = analysis_manager.get_analyzer(config)
        
        topics = analyzer.extract_topics(request.content)
        
        return {
            "topics": topics[:request.max_topics],
            "content_length": len(request.content),
            "analysis_type": "topic_extraction"
        }
        
    except Exception as e:
        logger.error(f"Topic extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic extraction failed: {str(e)}"
        )


@router.post("/summarize")
async def summarize_content(
    request: SummarizationRequest,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager)
) -> Dict[str, Any]:
    """
    Generate summary for content
    
    Function Description: Generate concise summary for text content
    Input Parameters: content (string), max_length (number)
    Return Parameters: Generated summary with metadata
    URL Address: /api/analysis/summarize
    Request Method: POST
    """
    try:
        config = AnalysisConfig()
        analyzer = analysis_manager.get_analyzer(config)
        
        summary = analyzer.generate_summary(request.content, request.max_length)
        keywords = analyzer.extract_keywords(request.content, 10)
        
        return {
            "summary": summary,
            "keywords": keywords,
            "original_length": len(request.content),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(request.content) if request.content else 0
        }
        
    except Exception as e:
        logger.error(f"Content summarization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content summarization failed: {str(e)}"
        )


@router.post("/estimate-processing-time")
async def estimate_processing_time(
    request: GenerateMindMapRequest,
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager),
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> Dict[str, Any]:
    """
    Estimate processing time for mind map generation
    
    Function Description: Estimate time required for video analysis and mind map generation
    Input Parameters: video_id (string), content_type (string, optional)
    Return Parameters: Processing time estimates for each stage
    URL Address: /api/analysis/estimate-processing-time
    Request Method: POST
    """
    try:
        # Create a mock transcript for estimation
        from app.services.stt_services.base import TranscriptResult
        
        # This would typically get video metadata to estimate transcript length
        estimated_duration = 600  # 10 minutes default
        estimated_segments = estimated_duration // 30  # Estimate segments
        
        mock_transcript = TranscriptResult(
            video_id=request.video_id,
            service_type=None,
            segments=[],
            duration=estimated_duration
        )
        
        # Estimate times
        stt_time = stt_manager.estimate_cost(None) * 60 if stt_manager else 30
        analysis_time = analysis_manager.estimate_processing_time(mock_transcript)
        
        total_time = stt_time + analysis_time
        
        return {
            "video_id": request.video_id,
            "estimated_duration": estimated_duration,
            "estimates": {
                "audio_extraction": 5.0,
                "speech_to_text": stt_time,
                "content_analysis": analysis_time,
                "total": total_time
            },
            "units": "seconds"
        }
        
    except Exception as e:
        logger.error(f"Processing time estimation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing time estimation failed: {str(e)}"
        )


@router.get("/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_manager: ContentAnalysisManager = Depends(get_analysis_manager)
) -> AnalysisStatusResponse:
    """
    Get content analysis service status
    
    Function Description: Get status and capabilities of content analysis service
    Input Parameters: None
    Return Parameters: Service status and feature information
    URL Address: /api/analysis/status
    Request Method: GET
    """
    try:
        status_data = analysis_manager.get_analysis_status()
        
        return AnalysisStatusResponse(
            service_name=status_data["service_name"],
            using_mock=status_data["using_mock"],
            analyzer_type=status_data["analyzer_type"],
            features=status_data["features"],
            supported_content_types=status_data["supported_content_types"],
            version=status_data["version"]
        )
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )