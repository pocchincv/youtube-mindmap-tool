"""
OpenAI Whisper API Speech-to-Text service implementation
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any

import openai
from openai import OpenAI

from .base import BaseSTTService, STTServiceType, STTServiceStatus, STTServiceInfo, STTServiceError
from .base import TranscriptResult, TranscriptSegment
from app.utils.audio_utils import AudioInfo


logger = logging.getLogger(__name__)


class OpenAIWhisperService(BaseSTTService):
    """OpenAI Whisper API Speech-to-Text service"""
    
    # OpenAI Whisper API limitations
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
    MAX_DURATION = 600  # 10 minutes
    COST_PER_MINUTE = 0.006  # $0.006 per minute
    
    SUPPORTED_LANGUAGES = [
        "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl", "ar",
        "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro", "da", "hu",
        "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa",
        "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", "mn",
        "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
        "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo", "ht", "ps", "tk", "nn",
        "mt", "sa", "lb", "my", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw",
        "su"
    ]
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI Whisper service
        
        Args:
            api_key: OpenAI API key
            **kwargs: Additional configuration
        """
        super().__init__(STTServiceType.OPENAI_WHISPER, api_key, **kwargs)
        
        # Initialize OpenAI client
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self._update_status(STTServiceStatus.AVAILABLE)
                logger.info("OpenAI Whisper service initialized successfully")
            except Exception as e:
                self._update_status(STTServiceStatus.ERROR, str(e))
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            self._update_status(STTServiceStatus.UNAVAILABLE, "No API key provided")
            logger.warning("OpenAI Whisper service unavailable: no API key")
    
    def transcribe_audio(self, audio_info: AudioInfo, language: Optional[str] = None, 
                        **kwargs) -> TranscriptResult:
        """
        Transcribe audio using OpenAI Whisper API
        
        Function Description: Transcribe audio file using OpenAI Whisper API with timestamps
        Input Parameters: audio_info (AudioInfo), language (string, optional)
        Return Parameters: TranscriptResult with timestamped segments
        URL Address: N/A (Service method)
        Request Method: N/A (Service method)
        """
        if not self.client:
            raise STTServiceError(
                "OpenAI client not initialized", 
                self.service_type, 
                "CLIENT_NOT_INITIALIZED"
            )
        
        # Validate audio file
        self._validate_audio(audio_info)
        
        processing_start = time.time()
        
        try:
            # Prepare API parameters
            transcription_params = {
                "model": kwargs.get("model", "whisper-1"),
                "response_format": "verbose_json",
                "timestamp_granularities": ["segment"]
            }
            
            # Add language if specified
            if language:
                if language not in self.SUPPORTED_LANGUAGES:
                    logger.warning(f"Language {language} might not be supported by OpenAI Whisper")
                transcription_params["language"] = language
            
            # Add optional parameters
            if "prompt" in kwargs:
                transcription_params["prompt"] = kwargs["prompt"]
            if "temperature" in kwargs:
                transcription_params["temperature"] = kwargs["temperature"]
            
            # Open audio file and call API
            with open(audio_info.file_path, "rb") as audio_file:
                logger.info(f"Starting OpenAI Whisper transcription for {audio_info.file_path}")
                
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **transcription_params
                )
            
            processing_time = time.time() - processing_start
            
            # Parse response and create transcript segments
            segments = self._parse_whisper_response(response)
            
            # Calculate cost
            duration_minutes = audio_info.duration / 60.0
            cost = duration_minutes * self.COST_PER_MINUTE
            
            # Detect language from response
            detected_language = getattr(response, 'language', None) or language
            
            result = TranscriptResult(
                video_id=os.path.basename(audio_info.file_path).split('_')[0],
                service_type=self.service_type,
                segments=segments,
                language=detected_language,
                confidence_score=self._calculate_average_confidence(segments),
                processing_time=processing_time,
                cost=cost,
                metadata={
                    "model": transcription_params["model"],
                    "audio_duration": audio_info.duration,
                    "segments_count": len(segments),
                    "response_format": "verbose_json"
                }
            )
            
            logger.info(f"OpenAI Whisper transcription completed: {len(segments)} segments, "
                       f"{processing_time:.2f}s processing time, ${cost:.4f} estimated cost")
            
            return result
            
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {e}"
            logger.error(error_msg)
            raise STTServiceError(error_msg, self.service_type, "API_ERROR")
        
        except openai.RateLimitError as e:
            error_msg = f"OpenAI rate limit exceeded: {e}"
            logger.error(error_msg)
            raise STTServiceError(error_msg, self.service_type, "RATE_LIMIT_EXCEEDED")
        
        except openai.AuthenticationError as e:
            error_msg = f"OpenAI authentication failed: {e}"
            logger.error(error_msg)
            self._update_status(STTServiceStatus.ERROR, error_msg)
            raise STTServiceError(error_msg, self.service_type, "AUTHENTICATION_ERROR")
        
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {e}"
            logger.error(error_msg)
            raise STTServiceError(error_msg, self.service_type, "TRANSCRIPTION_ERROR")
    
    def _parse_whisper_response(self, response) -> List[TranscriptSegment]:
        """Parse OpenAI Whisper API response into transcript segments"""
        segments = []
        
        # Handle both old and new response formats
        if hasattr(response, 'segments') and response.segments:
            # Verbose JSON format with segments
            for i, segment in enumerate(response.segments):
                segments.append(TranscriptSegment(
                    id=i,
                    start_time=segment.start,
                    end_time=segment.end,
                    text=segment.text.strip(),
                    confidence=getattr(segment, 'avg_logprob', None),
                    language=getattr(response, 'language', None)
                ))
        else:
            # Simple text format - create single segment
            full_text = getattr(response, 'text', str(response))
            if full_text:
                segments.append(TranscriptSegment(
                    id=0,
                    start_time=0.0,
                    end_time=0.0,  # Unknown duration
                    text=full_text.strip(),
                    confidence=None,
                    language=getattr(response, 'language', None)
                ))
        
        return segments
    
    def _calculate_average_confidence(self, segments: List[TranscriptSegment]) -> Optional[float]:
        """Calculate average confidence score from segments"""
        confidence_scores = [s.confidence for s in segments if s.confidence is not None]
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        return None
    
    def get_service_info(self) -> STTServiceInfo:
        """Get OpenAI Whisper service information"""
        return STTServiceInfo(
            service_type=self.service_type,
            name="OpenAI Whisper API",
            status=self._status,
            supported_languages=self.SUPPORTED_LANGUAGES,
            max_file_size=self.MAX_FILE_SIZE,
            max_duration=self.MAX_DURATION,
            cost_per_minute=self.COST_PER_MINUTE,
            supports_timestamps=True,
            supports_confidence=True,
            error_message=self._last_error
        )
    
    def check_availability(self) -> bool:
        """Check if OpenAI Whisper API is available"""
        if not self.client:
            self._update_status(STTServiceStatus.UNAVAILABLE, "Client not initialized")
            return False
        
        try:
            # Try to list models to test authentication
            models = self.client.models.list()
            
            # Check if whisper-1 model is available
            whisper_available = any(model.id == "whisper-1" for model in models.data)
            
            if whisper_available:
                self._update_status(STTServiceStatus.AVAILABLE)
                return True
            else:
                self._update_status(STTServiceStatus.UNAVAILABLE, "Whisper model not available")
                return False
                
        except openai.AuthenticationError as e:
            error_msg = f"Authentication failed: {e}"
            self._update_status(STTServiceStatus.ERROR, error_msg)
            return False
        
        except Exception as e:
            error_msg = f"Availability check failed: {e}"
            self._update_status(STTServiceStatus.ERROR, error_msg)
            return False
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Whisper models"""
        return ["whisper-1"]
    
    def estimate_processing_time(self, duration_minutes: float) -> float:
        """
        Estimate processing time based on audio duration
        
        Args:
            duration_minutes: Audio duration in minutes
            
        Returns:
            Estimated processing time in seconds
        """
        # OpenAI Whisper typically processes faster than real-time
        # Estimate: 1 minute of audio = ~10-30 seconds processing
        return duration_minutes * 20  # Conservative estimate