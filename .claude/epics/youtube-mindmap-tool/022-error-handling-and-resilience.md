---
id: 022-error-handling-and-resilience
title: Error Handling and System Resilience
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: medium
estimated_days: 2
dependencies: [015-video-processing-pipeline, 014-smart-search-system]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [error-handling, resilience, reliability, user-experience]
---

# Error Handling and System Resilience

## Description
Implement comprehensive error handling and system resilience features to ensure graceful degradation when external services fail, provide clear user feedback for errors, and maintain system stability under various failure conditions.

## Acceptance Criteria
- [ ] Graceful degradation when external APIs are unavailable
- [ ] User-friendly error messages with actionable guidance
- [ ] Automatic retry mechanisms with exponential backoff
- [ ] Fallback options when primary services fail
- [ ] Error boundary components to prevent React app crashes
- [ ] Comprehensive logging for debugging and monitoring
- [ ] Circuit breaker pattern for external service calls
- [ ] Offline mode support for basic functionality
- [ ] Data validation and sanitization at all input points
- [ ] Rate limiting and abuse prevention mechanisms
- [ ] Recovery procedures for corrupted data
- [ ] User notification system for service disruptions

## Technical Requirements

### Frontend Error Boundaries:
```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

class GlobalErrorBoundary extends Component<PropsWithChildren<{}>, ErrorBoundaryState> {
  constructor(props: PropsWithChildren<{}>) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      errorInfo
    });

    // Log error to monitoring service
    this.logErrorToService(error, errorInfo, this.state.errorId);
  }

  private logErrorToService(error: Error, errorInfo: ErrorInfo, errorId: string) {
    const errorData = {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Send to error tracking service
    fetch('/api/errors/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorData)
    }).catch(console.error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          errorId={this.state.errorId}
          onRetry={() => this.setState({ hasError: false, error: null, errorInfo: null })}
        />
      );
    }

    return this.props.children;
  }
}

const ErrorFallback: React.FC<{
  error: Error | null;
  errorId: string;
  onRetry: () => void;
}> = ({ error, errorId, onRetry }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center mb-4">
          <ExclamationTriangleIcon className="h-8 w-8 text-red-500 mr-3" />
          <h1 className="text-xl font-semibold text-gray-900">Something went wrong</h1>
        </div>
        
        <p className="text-gray-600 mb-4">
          We encountered an unexpected error. Our team has been notified and is working to fix this.
        </p>
        
        <div className="bg-gray-100 rounded p-3 mb-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Error ID:</span> {errorId}
          </p>
          {error && (
            <p className="text-sm text-gray-700 mt-1">
              <span className="font-medium">Error:</span> {error.message}
            </p>
          )}
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={onRetry}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
          >
            Reload Page
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Circuit Breaker Pattern:
```python
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import logging

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logging.info(f"Circuit breaker transitioning to HALF_OPEN for {func.__name__}")
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time is not None and
            datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        logging.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logging.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class CircuitOpenError(Exception):
    """Raised when circuit breaker is in OPEN state"""
    pass

# Usage example for external services
youtube_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
openai_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=180)

class ResilientYouTubeService:
    async def get_video_metadata(self, video_id: str):
        """Get video metadata with circuit breaker protection"""
        try:
            return await youtube_circuit_breaker.call(
                self._fetch_metadata, video_id
            )
        except CircuitOpenError:
            # Fallback to cached data or mock data
            logging.warning("YouTube API circuit breaker open, using fallback")
            return await self._get_cached_metadata(video_id)
        except Exception as e:
            logging.error(f"YouTube metadata fetch failed: {e}")
            raise ServiceUnavailableError("YouTube service temporarily unavailable")
    
    async def _fetch_metadata(self, video_id: str):
        # Actual YouTube API call implementation
        pass
    
    async def _get_cached_metadata(self, video_id: str):
        # Return cached metadata or basic fallback data
        pass
```

### Retry Mechanism with Exponential Backoff:
```python
import asyncio
import random
from typing import Callable, Any, Type, Tuple
from functools import wraps

def async_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 300.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True
):
    """Decorator for async retry with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed, raise the exception
                        logging.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise e
                    
                    # Calculate backoff time
                    backoff_time = min(
                        backoff_factor ** attempt,
                        max_backoff
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        backoff_time *= (0.5 + random.random() * 0.5)
                    
                    logging.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {backoff_time:.2f} seconds: {e}"
                    )
                    
                    await asyncio.sleep(backoff_time)
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator

# Usage example
class ResilientSTTService:
    @async_retry(
        max_attempts=3,
        exceptions=(OpenAIAPIError, APIConnectionError)
    )
    async def transcribe_with_openai(self, audio_data: bytes):
        """Transcribe audio with retry logic"""
        return await self._call_openai_api(audio_data)
    
    async def transcribe_with_fallback(self, audio_data: bytes):
        """Transcribe with multiple service fallbacks"""
        services = [
            ("OpenAI", self.transcribe_with_openai),
            ("Google", self.transcribe_with_google),
            ("Local Whisper", self.transcribe_with_local_whisper)
        ]
        
        last_error = None
        
        for service_name, service_func in services:
            try:
                logging.info(f"Attempting transcription with {service_name}")
                result = await service_func(audio_data)
                logging.info(f"Transcription successful with {service_name}")
                return result
                
            except Exception as e:
                logging.warning(f"Transcription failed with {service_name}: {e}")
                last_error = e
                continue
        
        # All services failed
        raise ServiceUnavailableError(
            f"All transcription services failed. Last error: {last_error}"
        )
```

### User-Friendly Error Messages:
```typescript
interface ErrorMessage {
  title: string;
  message: string;
  action?: {
    label: string;
    handler: () => void;
  };
  severity: 'error' | 'warning' | 'info';
}

class ErrorMessageManager {
  private static errorMessages: Record<string, ErrorMessage> = {
    // Network errors
    'NETWORK_ERROR': {
      title: 'Connection Problem',
      message: 'Unable to connect to our servers. Please check your internet connection and try again.',
      action: {
        label: 'Retry',
        handler: () => window.location.reload()
      },
      severity: 'error'
    },
    
    // YouTube API errors
    'YOUTUBE_VIDEO_NOT_FOUND': {
      title: 'Video Not Found',
      message: 'The YouTube video could not be found. Please check the URL and make sure the video is public.',
      severity: 'error'
    },
    
    'YOUTUBE_PRIVATE_VIDEO': {
      title: 'Private Video',
      message: 'This video is private and cannot be processed. Please use a public video.',
      severity: 'error'
    },
    
    'YOUTUBE_QUOTA_EXCEEDED': {
      title: 'Service Temporarily Limited',
      message: 'We\'ve reached our daily limit for YouTube requests. Please try again tomorrow.',
      severity: 'warning'
    },
    
    // Processing errors
    'STT_SERVICE_UNAVAILABLE': {
      title: 'Processing Service Unavailable',
      message: 'Our speech-to-text service is temporarily unavailable. We\'re working to restore it.',
      action: {
        label: 'Try Alternative Service',
        handler: () => console.log('Switch to fallback STT service')
      },
      severity: 'warning'
    },
    
    'PROCESSING_TIMEOUT': {
      title: 'Processing Taking Longer Than Expected',
      message: 'This video is taking longer to process than usual. You can wait or try with a shorter video.',
      severity: 'info'
    },
    
    // Authentication errors
    'AUTH_SESSION_EXPIRED': {
      title: 'Session Expired',
      message: 'Your session has expired. Please sign in again to continue.',
      action: {
        label: 'Sign In',
        handler: () => console.log('Redirect to login')
      },
      severity: 'warning'
    }
  };
  
  static getErrorMessage(errorCode: string): ErrorMessage {
    return this.errorMessages[errorCode] || {
      title: 'Unexpected Error',
      message: 'An unexpected error occurred. Please try again or contact support if the problem persists.',
      severity: 'error'
    };
  }
  
  static formatAPIError(error: any): ErrorMessage {
    if (error.response?.status === 404) {
      return this.getErrorMessage('YOUTUBE_VIDEO_NOT_FOUND');
    } else if (error.response?.status === 429) {
      return this.getErrorMessage('YOUTUBE_QUOTA_EXCEEDED');
    } else if (error.response?.status === 401) {
      return this.getErrorMessage('AUTH_SESSION_EXPIRED');
    } else if (!navigator.onLine) {
      return this.getErrorMessage('NETWORK_ERROR');
    }
    
    return this.getErrorMessage('UNKNOWN_ERROR');
  }
}

// Error notification component
const ErrorNotification: React.FC<{
  error: ErrorMessage;
  onClose: () => void;
}> = ({ error, onClose }) => {
  const severityStyles = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  };
  
  return (
    <div className={`border rounded-lg p-4 mb-4 ${severityStyles[error.severity]}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-semibold mb-1">{error.title}</h3>
          <p className="text-sm">{error.message}</p>
          
          {error.action && (
            <button
              onClick={error.action.handler}
              className="mt-2 text-sm underline hover:no-underline"
            >
              {error.action.label}
            </button>
          )}
        </div>
        
        <button
          onClick={onClose}
          className="ml-4 text-gray-500 hover:text-gray-700"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};
```

### Data Validation and Sanitization:
```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re
from urllib.parse import urlparse

class YouTubeURLValidator(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    
    @validator('url')
    def validate_youtube_url(cls, v):
        """Validate and extract YouTube video ID"""
        if not isinstance(v, str):
            raise ValueError('URL must be a string')
        
        # Sanitize URL
        v = v.strip()
        
        # YouTube URL patterns
        youtube_patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, v)
            if match:
                return v
        
        raise ValueError('Invalid YouTube URL format')

class PlaylistCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    user_id: str = Field(..., description="User ID")
    
    @validator('name')
    def validate_playlist_name(cls, v):
        """Validate and sanitize playlist name"""
        if not v or not v.strip():
            raise ValueError('Playlist name cannot be empty')
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\']', '', v.strip())
        
        if len(sanitized) < 1:
            raise ValueError('Playlist name contains only invalid characters')
        
        return sanitized

class SearchQueryValidator(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    filters: Optional[dict] = Field(default_factory=dict)
    
    @validator('query')
    def validate_search_query(cls, v):
        """Validate and sanitize search query"""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        
        # Basic sanitization
        sanitized = v.strip()
        
        # Remove potential injection attempts
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>'
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
```

### Error Handling APIs:
```
/**
* Error Reporting Endpoint
* Report client-side errors for monitoring and debugging
* Input Parameters: error_data (object) with error details
* Return Parameters: ErrorReport with tracking ID
* URL Address: /api/errors/report
* Request Method: POST
**/

/**
* Service Status Check
* Check status of all external services and dependencies
* Input Parameters: None
* Return Parameters: ServiceStatus with health of each service
* URL Address: /api/status/services
* Request Method: GET
**/

/**
* Error Recovery Actions
* Provide recovery actions for specific error conditions
* Input Parameters: error_code (string), context (object)
* Return Parameters: RecoveryActions with available options
* URL Address: /api/errors/recovery/{error_code}
* Request Method: GET
**/
```

## Definition of Done
- All external API calls are protected by circuit breaker pattern
- User-friendly error messages are displayed for all error conditions
- Retry mechanisms handle transient failures automatically
- Error boundaries prevent React app crashes and provide recovery options
- Comprehensive error logging captures sufficient debugging information
- Fallback mechanisms maintain basic functionality when services are unavailable
- Data validation prevents malformed or malicious input from causing errors
- Rate limiting protects against abuse and overload conditions
- Users receive clear guidance on how to resolve or work around errors
- System gracefully degrades functionality rather than failing completely
- Error recovery procedures restore normal operation automatically when possible
- Monitoring alerts notify administrators of critical system issues