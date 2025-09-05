"""
Speech-to-Text Services Manager with fallback mechanisms
"""

import os
import logging
from typing import Optional, Dict, List, Any
from enum import Enum

from .base import BaseSTTService, STTServiceType, STTServiceStatus, STTServiceInfo, STTServiceError, MockSTTService
from .base import TranscriptResult, TranscriptSegment
from .openai_service import OpenAIWhisperService
from .local_whisper import LocalWhisperService
from app.utils.audio_utils import AudioInfo


logger = logging.getLogger(__name__)


class STTServiceManager:
    """Manages multiple STT services with fallback mechanisms"""
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize STT service manager
        
        Args:
            use_mock: Use mock services for development
        """
        self.use_mock = use_mock or os.getenv('USE_MOCK_STT', '').lower() == 'true'
        self.services: Dict[STTServiceType, BaseSTTService] = {}
        self.fallback_order: List[STTServiceType] = []
        
        self._initialize_services()
        self._setup_fallback_order()
        
        logger.info(f"STT Service Manager initialized with {len(self.services)} services")
    
    def _initialize_services(self):
        """Initialize all available STT services"""
        if self.use_mock:
            # Use mock service for development
            self.services[STTServiceType.OPENAI_WHISPER] = MockSTTService()
            logger.info("Initialized mock STT services")
            return
        
        # Initialize OpenAI Whisper service
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                self.services[STTServiceType.OPENAI_WHISPER] = OpenAIWhisperService(
                    api_key=openai_api_key
                )
                logger.info("Initialized OpenAI Whisper service")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI Whisper service: {e}")
        
        # Initialize Local Whisper service
        try:
            self.services[STTServiceType.LOCAL_WHISPER] = LocalWhisperService(
                model_size=os.getenv('WHISPER_MODEL_SIZE', 'base')
            )
            logger.info("Initialized Local Whisper service")
        except Exception as e:
            logger.warning(f"Failed to initialize Local Whisper service: {e}")
        
        # Add mock service as fallback if no real services available
        if not self.services:
            self.services[STTServiceType.OPENAI_WHISPER] = MockSTTService()
            logger.warning("No real STT services available, using mock service")
    
    def _setup_fallback_order(self):
        """Setup fallback order for STT services"""
        # Preferred order: OpenAI -> Local Whisper -> Mock
        preferred_order = [
            STTServiceType.OPENAI_WHISPER,
            STTServiceType.LOCAL_WHISPER,
            STTServiceType.GOOGLE_STT,  # If implemented
            STTServiceType.BREEZE_ASR   # If implemented
        ]
        
        # Only include services that are actually initialized
        self.fallback_order = [
            service_type for service_type in preferred_order 
            if service_type in self.services
        ]
        
        logger.info(f"STT fallback order: {[s.value for s in self.fallback_order]}")
    
    def transcribe_audio(self, audio_info: AudioInfo, 
                        preferred_service: Optional[STTServiceType] = None,
                        language: Optional[str] = None,
                        **kwargs) -> TranscriptResult:
        """
        Transcribe audio using STT services with fallback
        
        Function Description: Transcribe audio with automatic service fallback
        Input Parameters: audio_info (AudioInfo), preferred_service (STTServiceType, optional), language (string, optional)
        Return Parameters: TranscriptResult with transcription
        URL Address: N/A (Service method)
        Request Method: N/A (Service method)
        """
        if not self.services:
            raise STTServiceError(
                "No STT services available",
                STTServiceType.OPENAI_WHISPER,
                "NO_SERVICES_AVAILABLE"
            )
        
        # Determine service order
        services_to_try = self._get_service_order(preferred_service)
        
        last_error = None
        
        for service_type in services_to_try:
            service = self.services.get(service_type)
            if not service:
                continue
            
            # Check if service is available
            if not service.check_availability():
                logger.warning(f"STT service {service_type.value} is not available, trying next")
                continue
            
            try:
                logger.info(f"Attempting transcription with {service_type.value}")
                result = service.transcribe_audio(audio_info, language, **kwargs)
                
                logger.info(f"Transcription successful with {service_type.value}")
                return result
                
            except STTServiceError as e:
                logger.warning(f"STT service {service_type.value} failed: {e.message}")
                last_error = e
                continue
            
            except Exception as e:
                logger.error(f"Unexpected error with {service_type.value}: {e}")
                last_error = STTServiceError(
                    f"Unexpected error: {str(e)}",
                    service_type,
                    "UNEXPECTED_ERROR"
                )
                continue
        
        # All services failed
        error_msg = f"All STT services failed. Last error: {last_error.message if last_error else 'Unknown'}"
        raise STTServiceError(error_msg, STTServiceType.OPENAI_WHISPER, "ALL_SERVICES_FAILED")
    
    def _get_service_order(self, preferred_service: Optional[STTServiceType] = None) -> List[STTServiceType]:
        """Get service order for transcription attempts"""
        if preferred_service and preferred_service in self.services:
            # Put preferred service first, then fallbacks
            order = [preferred_service]
            order.extend([s for s in self.fallback_order if s != preferred_service])
            return order
        
        return self.fallback_order.copy()
    
    def get_service_info(self, service_type: STTServiceType) -> Optional[STTServiceInfo]:
        """Get information about a specific STT service"""
        service = self.services.get(service_type)
        if service:
            return service.get_service_info()
        return None
    
    def get_all_services_info(self) -> Dict[str, STTServiceInfo]:
        """Get information about all available STT services"""
        info = {}
        for service_type, service in self.services.items():
            info[service_type.value] = service.get_service_info()
        return info
    
    def check_service_availability(self, service_type: STTServiceType) -> bool:
        """Check if a specific service is available"""
        service = self.services.get(service_type)
        if service:
            return service.check_availability()
        return False
    
    def get_available_services(self) -> List[STTServiceType]:
        """Get list of available STT services"""
        available = []
        for service_type, service in self.services.items():
            if service.check_availability():
                available.append(service_type)
        return available
    
    def estimate_cost(self, audio_info: AudioInfo, 
                     service_type: Optional[STTServiceType] = None) -> Optional[float]:
        """
        Estimate transcription cost for audio
        
        Args:
            audio_info: Audio file information
            service_type: Specific service to estimate for (default: first available)
            
        Returns:
            Estimated cost in USD, None if free service
        """
        if service_type:
            service = self.services.get(service_type)
        else:
            # Use first available service
            available_services = self.get_available_services()
            if not available_services:
                return None
            service = self.services.get(available_services[0])
        
        if service:
            duration_minutes = audio_info.duration / 60.0
            return service.estimate_cost(duration_minutes)
        
        return None
    
    def get_supported_languages(self, service_type: Optional[STTServiceType] = None) -> List[str]:
        """
        Get supported languages for service
        
        Args:
            service_type: Specific service (default: first available)
            
        Returns:
            List of supported language codes
        """
        if service_type:
            service = self.services.get(service_type)
        else:
            # Use first available service
            available_services = self.get_available_services()
            if not available_services:
                return []
            service = self.services.get(available_services[0])
        
        if service:
            return service.get_supported_languages()
        
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all STT services
        
        Returns:
            Health status for all services
        """
        health_status = {
            "services_count": len(self.services),
            "available_services": len(self.get_available_services()),
            "using_mock": self.use_mock,
            "fallback_order": [s.value for s in self.fallback_order],
            "services": {}
        }
        
        for service_type, service in self.services.items():
            service_info = service.get_service_info()
            health_status["services"][service_type.value] = {
                "name": service_info.name,
                "status": service_info.status.value,
                "available": service.check_availability(),
                "error": service_info.error_message
            }
        
        return health_status