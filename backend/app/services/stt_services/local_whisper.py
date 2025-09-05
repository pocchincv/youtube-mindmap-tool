"""
Local Whisper model Speech-to-Text service implementation
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

from .base import BaseSTTService, STTServiceType, STTServiceStatus, STTServiceInfo, STTServiceError
from .base import TranscriptResult, TranscriptSegment
from app.utils.audio_utils import AudioInfo


logger = logging.getLogger(__name__)


class LocalWhisperService(BaseSTTService):
    """Local Whisper model Speech-to-Text service"""
    
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    SUPPORTED_LANGUAGES = ["en", "zh", "es", "fr", "de", "it", "ja", "ko", "pt", "ru"]  # Common languages
    
    def __init__(self, model_size: str = "base", **kwargs):
        """
        Initialize Local Whisper service
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            **kwargs: Additional configuration
        """
        super().__init__(STTServiceType.LOCAL_WHISPER, **kwargs)
        
        self.model_size = model_size
        self.model = None
        
        if not WHISPER_AVAILABLE:
            self._update_status(STTServiceStatus.UNAVAILABLE, "Whisper package not installed")
            logger.warning("Local Whisper unavailable: whisper package not installed")
            return
        
        if model_size not in self.AVAILABLE_MODELS:
            self._update_status(STTServiceStatus.ERROR, f"Invalid model size: {model_size}")
            return
        
        # Try to load the model
        try:
            self.model = whisper.load_model(model_size)
            self._update_status(STTServiceStatus.AVAILABLE)
            logger.info(f"Local Whisper service initialized with {model_size} model")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {e}"
            self._update_status(STTServiceStatus.ERROR, error_msg)
            logger.error(error_msg)
    
    def transcribe_audio(self, audio_info: AudioInfo, language: Optional[str] = None, 
                        **kwargs) -> TranscriptResult:
        """
        Transcribe audio using local Whisper model
        
        Function Description: Transcribe audio file using local Whisper model
        Input Parameters: audio_info (AudioInfo), language (string, optional)
        Return Parameters: TranscriptResult with timestamped segments
        URL Address: N/A (Service method)
        Request Method: N/A (Service method)
        """
        if not self.model:
            raise STTServiceError(
                "Local Whisper model not loaded", 
                self.service_type, 
                "MODEL_NOT_LOADED"
            )
        
        self._validate_audio(audio_info)
        
        processing_start = time.time()
        
        try:
            # Prepare transcription options
            options = {
                "language": language,
                "task": kwargs.get("task", "transcribe"),
                "fp16": kwargs.get("fp16", False),
                "verbose": False
            }
            
            logger.info(f"Starting local Whisper transcription for {audio_info.file_path}")
            
            # Transcribe audio
            result = self.model.transcribe(audio_info.file_path, **options)
            
            processing_time = time.time() - processing_start
            
            # Parse result into segments
            segments = self._parse_whisper_result(result)
            
            transcript_result = TranscriptResult(
                video_id=os.path.basename(audio_info.file_path).split('_')[0],
                service_type=self.service_type,
                segments=segments,
                language=result.get("language", language),
                confidence_score=self._calculate_average_confidence(segments),
                processing_time=processing_time,
                cost=0.0,  # Local processing is free
                metadata={
                    "model_size": self.model_size,
                    "audio_duration": audio_info.duration,
                    "segments_count": len(segments),
                    "detected_language": result.get("language")
                }
            )
            
            logger.info(f"Local Whisper transcription completed: {len(segments)} segments, "
                       f"{processing_time:.2f}s processing time")
            
            return transcript_result
            
        except Exception as e:
            error_msg = f"Local Whisper transcription failed: {e}"
            logger.error(error_msg)
            raise STTServiceError(error_msg, self.service_type, "TRANSCRIPTION_ERROR")
    
    def _parse_whisper_result(self, result: Dict[str, Any]) -> List[TranscriptSegment]:
        """Parse local Whisper result into transcript segments"""
        segments = []
        
        if "segments" in result:
            for i, segment in enumerate(result["segments"]):
                segments.append(TranscriptSegment(
                    id=i,
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("avg_logprob"),
                    language=result.get("language")
                ))
        else:
            # Fallback: create single segment from full text
            full_text = result.get("text", "")
            if full_text:
                segments.append(TranscriptSegment(
                    id=0,
                    start_time=0.0,
                    end_time=0.0,
                    text=full_text.strip(),
                    confidence=None,
                    language=result.get("language")
                ))
        
        return segments
    
    def _calculate_average_confidence(self, segments: List[TranscriptSegment]) -> Optional[float]:
        """Calculate average confidence score from segments"""
        confidence_scores = [s.confidence for s in segments if s.confidence is not None]
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        return None
    
    def get_service_info(self) -> STTServiceInfo:
        """Get Local Whisper service information"""
        return STTServiceInfo(
            service_type=self.service_type,
            name=f"Local Whisper ({self.model_size})",
            status=self._status,
            supported_languages=self.SUPPORTED_LANGUAGES,
            max_file_size=None,  # No file size limit
            max_duration=None,   # No duration limit
            cost_per_minute=0.0, # Free
            supports_timestamps=True,
            supports_confidence=True,
            error_message=self._last_error
        )
    
    def check_availability(self) -> bool:
        """Check if Local Whisper is available"""
        if not WHISPER_AVAILABLE:
            self._update_status(STTServiceStatus.UNAVAILABLE, "Whisper package not installed")
            return False
        
        if not self.model:
            self._update_status(STTServiceStatus.ERROR, "Model not loaded")
            return False
        
        self._update_status(STTServiceStatus.AVAILABLE)
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return self.AVAILABLE_MODELS