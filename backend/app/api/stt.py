"""
Speech-to-Text API endpoints
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field

from app.services.stt_services.manager import STTServiceManager
from app.services.stt_services.base import STTServiceType, STTServiceError
from app.utils.audio_utils import YouTubeAudioExtractor, AudioInfo, AudioProcessingError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])


# Request/Response Models
class TranscribeVideoRequest(BaseModel):
    """Request model for video transcription"""
    video_id: str = Field(..., description="YouTube video ID")
    language: Optional[str] = Field(None, description="Target language code (optional)")
    service: Optional[str] = Field(None, description="Preferred STT service")


class TranscriptSegmentResponse(BaseModel):
    """Response model for transcript segment"""
    id: int
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Response model for transcript result"""
    video_id: str
    service_type: str
    segments: list[TranscriptSegmentResponse]
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class STTServiceStatusResponse(BaseModel):
    """Response model for STT service status"""
    name: str
    status: str
    available: bool
    error: Optional[str] = None


class STTHealthResponse(BaseModel):
    """Response model for STT health check"""
    services_count: int
    available_services: int
    using_mock: bool
    fallback_order: list[str]
    services: Dict[str, STTServiceStatusResponse]


# Dependency to get STT service manager
def get_stt_manager() -> STTServiceManager:
    """Get STT service manager instance"""
    return STTServiceManager()


@router.post("/transcribe/video", response_model=TranscriptResponse)
async def transcribe_video(
    request: TranscribeVideoRequest,
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> TranscriptResponse:
    """
    Transcribe YouTube video audio using STT services
    
    Function Description: Extract and transcribe YouTube video audio
    Input Parameters: video_id (string), language (string, optional), service (string, optional)
    Return Parameters: TranscriptResponse with timestamped segments
    URL Address: /api/stt/transcribe/video
    Request Method: POST
    """
    try:
        # Parse preferred service
        preferred_service = None
        if request.service:
            try:
                preferred_service = STTServiceType(request.service)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid service type: {request.service}"
                )
        
        # Extract audio from YouTube video
        audio_extractor = YouTubeAudioExtractor()
        
        try:
            logger.info(f"Extracting audio for video: {request.video_id}")
            audio_info = audio_extractor.extract_audio(request.video_id, format="wav")
            
            logger.info(f"Audio extracted: {audio_info.duration:.2f}s, {audio_info.file_path}")
            
            # Transcribe audio
            result = stt_manager.transcribe_audio(
                audio_info=audio_info,
                preferred_service=preferred_service,
                language=request.language
            )
            
            logger.info(f"Transcription completed with {result.service_type.value}")
            
            # Convert to response format
            segments = [
                TranscriptSegmentResponse(
                    id=seg.id,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=seg.text,
                    confidence=seg.confidence,
                    language=seg.language
                )
                for seg in result.segments
            ]
            
            return TranscriptResponse(
                video_id=result.video_id,
                service_type=result.service_type.value,
                segments=segments,
                language=result.language,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                cost=result.cost,
                metadata=result.metadata
            )
            
        finally:
            # Clean up temporary audio files
            audio_extractor.cleanup_temp_files()
    
    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Audio processing failed: {e.message}"
        )
    
    except STTServiceError as e:
        logger.error(f"STT service error: {e}")
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        if e.error_code == "ALL_SERVICES_FAILED":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif e.error_code == "RATE_LIMIT_EXCEEDED":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif e.error_code == "AUTHENTICATION_ERROR":
            status_code = status.HTTP_401_UNAUTHORIZED
        
        raise HTTPException(status_code=status_code, detail=e.message)
    
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/transcribe/upload", response_model=TranscriptResponse)
async def transcribe_uploaded_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    service: Optional[str] = None,
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> TranscriptResponse:
    """
    Transcribe uploaded audio file
    
    Function Description: Transcribe user-uploaded audio file
    Input Parameters: file (audio file), language (string, optional), service (string, optional)  
    Return Parameters: TranscriptResponse with timestamped segments
    URL Address: /api/stt/transcribe/upload
    Request Method: POST
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Parse preferred service
        preferred_service = None
        if service:
            try:
                preferred_service = STTServiceType(service)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid service type: {service}"
                )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Create AudioInfo
            audio_info = AudioInfo(
                file_path=temp_file_path,
                duration=0.0,  # Will be determined by STT service
                format="wav",
                sample_rate=16000,
                channels=1,
                size_bytes=len(content)
            )
            
            # Transcribe audio
            result = stt_manager.transcribe_audio(
                audio_info=audio_info,
                preferred_service=preferred_service,
                language=language
            )
            
            # Convert to response format
            segments = [
                TranscriptSegmentResponse(
                    id=seg.id,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=seg.text,
                    confidence=seg.confidence,
                    language=seg.language
                )
                for seg in result.segments
            ]
            
            return TranscriptResponse(
                video_id="uploaded_file",
                service_type=result.service_type.value,
                segments=segments,
                language=result.language,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                cost=result.cost,
                metadata=result.metadata
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except STTServiceError as e:
        logger.error(f"STT service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during upload transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get("/status", response_model=STTHealthResponse)
async def get_stt_status(
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> STTHealthResponse:
    """
    Get STT services status and health check
    
    Function Description: Get status of all STT services
    Input Parameters: None
    Return Parameters: STTHealthResponse with service status
    URL Address: /api/stt/status
    Request Method: GET
    """
    try:
        health_status = stt_manager.health_check()
        
        # Convert service statuses
        services = {}
        for service_name, service_data in health_status["services"].items():
            services[service_name] = STTServiceStatusResponse(
                name=service_data["name"],
                status=service_data["status"],
                available=service_data["available"],
                error=service_data.get("error")
            )
        
        return STTHealthResponse(
            services_count=health_status["services_count"],
            available_services=health_status["available_services"],
            using_mock=health_status["using_mock"],
            fallback_order=health_status["fallback_order"],
            services=services
        )
    
    except Exception as e:
        logger.error(f"Error getting STT status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get STT status: {str(e)}"
        )


@router.get("/services")
async def get_available_services(
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> Dict[str, Any]:
    """
    Get list of available STT services
    
    Function Description: Get information about available STT services
    Input Parameters: None
    Return Parameters: Dictionary with service information
    URL Address: /api/stt/services
    Request Method: GET
    """
    try:
        available_services = stt_manager.get_available_services()
        all_services_info = stt_manager.get_all_services_info()
        
        return {
            "available_services": [service.value for service in available_services],
            "all_services": {
                service_type: {
                    "name": info.name,
                    "status": info.status.value,
                    "supported_languages": info.supported_languages,
                    "cost_per_minute": info.cost_per_minute,
                    "max_file_size": info.max_file_size,
                    "max_duration": info.max_duration,
                    "supports_timestamps": info.supports_timestamps,
                    "supports_confidence": info.supports_confidence
                }
                for service_type, info in all_services_info.items()
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting available services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service information: {str(e)}"
        )


@router.post("/estimate-cost")
async def estimate_transcription_cost(
    request: TranscribeVideoRequest,
    stt_manager: STTServiceManager = Depends(get_stt_manager)
) -> Dict[str, Any]:
    """
    Estimate transcription cost for a video
    
    Function Description: Estimate cost for transcribing a YouTube video
    Input Parameters: video_id (string), service (string, optional)
    Return Parameters: Cost estimation information
    URL Address: /api/stt/estimate-cost
    Request Method: POST
    """
    try:
        # Parse service type
        service_type = None
        if request.service:
            try:
                service_type = STTServiceType(request.service)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid service type: {request.service}"
                )
        
        # Get video duration (simplified - would need actual video metadata)
        # For now, return mock estimation
        estimated_duration = 600  # 10 minutes as example
        
        # Mock AudioInfo for cost estimation
        audio_info = AudioInfo(
            file_path="",
            duration=estimated_duration,
            format="wav",
            sample_rate=16000,
            channels=1
        )
        
        cost = stt_manager.estimate_cost(audio_info, service_type)
        
        return {
            "video_id": request.video_id,
            "estimated_duration_minutes": estimated_duration / 60,
            "service_type": service_type.value if service_type else "auto",
            "estimated_cost_usd": cost,
            "currency": "USD"
        }
    
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate cost: {str(e)}"
        )