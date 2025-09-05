"""
Base classes and interfaces for Speech-to-Text services
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.utils.audio_utils import AudioInfo


logger = logging.getLogger(__name__)


class STTServiceType(Enum):
    """STT service types"""
    OPENAI_WHISPER = "openai_whisper"
    GOOGLE_STT = "google_stt"
    LOCAL_WHISPER = "local_whisper"
    BREEZE_ASR = "breeze_asr"


class STTServiceStatus(Enum):
    """STT service status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class TranscriptSegment:
    """Single transcript segment with timing"""
    id: int
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time


@dataclass
class TranscriptResult:
    """Complete transcript result from STT service"""
    video_id: str
    service_type: STTServiceType
    segments: List[TranscriptSegment]
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def full_text(self) -> str:
        """Get full transcript text"""
        return " ".join([segment.text for segment in self.segments])
    
    @property
    def duration(self) -> float:
        """Get total transcript duration"""
        if not self.segments:
            return 0.0
        return max(segment.end_time for segment in self.segments)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "video_id": self.video_id,
            "service_type": self.service_type.value,
            "segments": [
                {
                    "id": seg.id,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "language": seg.language
                }
                for seg in self.segments
            ],
            "language": self.language,
            "confidence_score": self.confidence_score,
            "processing_time": self.processing_time,
            "cost": self.cost,
            "metadata": self.metadata or {}
        }


@dataclass
class STTServiceInfo:
    """STT service information and capabilities"""
    service_type: STTServiceType
    name: str
    status: STTServiceStatus
    supported_languages: List[str]
    max_file_size: Optional[int] = None  # Max file size in bytes
    max_duration: Optional[int] = None   # Max duration in seconds
    cost_per_minute: Optional[float] = None
    supports_timestamps: bool = True
    supports_confidence: bool = False
    error_message: Optional[str] = None


class STTServiceError(Exception):
    """STT service related errors"""
    def __init__(self, message: str, service_type: STTServiceType, error_code: Optional[str] = None):
        self.message = message
        self.service_type = service_type
        self.error_code = error_code
        super().__init__(message)


class BaseSTTService(ABC):
    """Base class for all STT service implementations"""
    
    def __init__(self, service_type: STTServiceType, api_key: Optional[str] = None, **kwargs):
        self.service_type = service_type
        self.api_key = api_key
        self.config = kwargs
        self._status = STTServiceStatus.UNKNOWN
        self._last_error: Optional[str] = None
    
    @abstractmethod
    def transcribe_audio(self, audio_info: AudioInfo, language: Optional[str] = None, 
                        **kwargs) -> TranscriptResult:
        """
        Transcribe audio file to text with timestamps
        
        Args:
            audio_info: Audio file information
            language: Target language code (optional)
            **kwargs: Additional service-specific parameters
            
        Returns:
            TranscriptResult with segments and metadata
            
        Raises:
            STTServiceError: If transcription fails
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> STTServiceInfo:
        """
        Get service information and status
        
        Returns:
            STTServiceInfo with service capabilities
        """
        pass
    
    @abstractmethod
    def check_availability(self) -> bool:
        """
        Check if service is available
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.get_service_info().supported_languages
    
    def estimate_cost(self, duration_minutes: float) -> Optional[float]:
        """
        Estimate transcription cost
        
        Args:
            duration_minutes: Audio duration in minutes
            
        Returns:
            Estimated cost in USD, None if free service
        """
        service_info = self.get_service_info()
        if service_info.cost_per_minute:
            return duration_minutes * service_info.cost_per_minute
        return None
    
    def _validate_audio(self, audio_info: AudioInfo) -> None:
        """
        Validate audio file against service limitations
        
        Args:
            audio_info: Audio file to validate
            
        Raises:
            STTServiceError: If audio file doesn't meet requirements
        """
        service_info = self.get_service_info()
        
        # Check file size
        if service_info.max_file_size and audio_info.size_bytes:
            if audio_info.size_bytes > service_info.max_file_size:
                raise STTServiceError(
                    f"Audio file too large: {audio_info.size_bytes} bytes > {service_info.max_file_size} bytes",
                    self.service_type,
                    "FILE_TOO_LARGE"
                )
        
        # Check duration
        if service_info.max_duration:
            if audio_info.duration > service_info.max_duration:
                raise STTServiceError(
                    f"Audio duration too long: {audio_info.duration}s > {service_info.max_duration}s",
                    self.service_type,
                    "DURATION_TOO_LONG"
                )
        
        # Check if file exists
        import os
        if not os.path.exists(audio_info.file_path):
            raise STTServiceError(
                f"Audio file not found: {audio_info.file_path}",
                self.service_type,
                "FILE_NOT_FOUND"
            )
    
    def _update_status(self, status: STTServiceStatus, error_message: Optional[str] = None):
        """Update service status"""
        self._status = status
        self._last_error = error_message
        if error_message:
            logger.warning(f"STT service {self.service_type.value} status: {status.value} - {error_message}")


class MockSTTService(BaseSTTService):
    """Mock STT service for development and testing"""
    
    def __init__(self, **kwargs):
        super().__init__(STTServiceType.OPENAI_WHISPER, **kwargs)
        self._status = STTServiceStatus.AVAILABLE
    
    def transcribe_audio(self, audio_info: AudioInfo, language: Optional[str] = None, 
                        **kwargs) -> TranscriptResult:
        """Generate mock transcript"""
        import time
        import random
        
        # Simulate processing time
        processing_start = time.time()
        time.sleep(0.5)  # Mock processing delay
        
        # Generate mock segments
        segments = []
        duration = audio_info.duration
        segment_length = 10.0  # 10 second segments
        
        mock_texts = [
            "Welcome to this video about interesting topics.",
            "Today we'll be discussing various concepts and ideas.",
            "This is an automatically generated transcript for demonstration purposes.",
            "The content includes detailed explanations and examples.",
            "We hope you find this information useful and informative.",
            "Thank you for watching and please subscribe for more content."
        ]
        
        current_time = 0.0
        segment_id = 0
        
        while current_time < duration:
            end_time = min(current_time + segment_length, duration)
            text = mock_texts[segment_id % len(mock_texts)]
            
            segment = TranscriptSegment(
                id=segment_id,
                start_time=current_time,
                end_time=end_time,
                text=text,
                confidence=random.uniform(0.85, 0.99),
                language=language or "en"
            )
            
            segments.append(segment)
            current_time = end_time
            segment_id += 1
        
        processing_time = time.time() - processing_start
        
        return TranscriptResult(
            video_id="mock_video",
            service_type=self.service_type,
            segments=segments,
            language=language or "en",
            confidence_score=sum(s.confidence or 0.9 for s in segments) / len(segments),
            processing_time=processing_time,
            cost=0.0,  # Mock service is free
            metadata={
                "mock": True,
                "segments_count": len(segments),
                "audio_duration": duration
            }
        )
    
    def get_service_info(self) -> STTServiceInfo:
        """Get mock service information"""
        return STTServiceInfo(
            service_type=self.service_type,
            name="Mock STT Service",
            status=self._status,
            supported_languages=["en", "zh", "es", "fr", "de", "ja", "ko"],
            max_file_size=None,
            max_duration=None,
            cost_per_minute=0.0,
            supports_timestamps=True,
            supports_confidence=True,
            error_message=self._last_error
        )
    
    def check_availability(self) -> bool:
        """Mock service is always available"""
        self._update_status(STTServiceStatus.AVAILABLE)
        return True