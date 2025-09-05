"""
Audio processing utilities for YouTube video extraction and STT processing
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

import yt_dlp
from pydub import AudioSegment


logger = logging.getLogger(__name__)


@dataclass
class AudioInfo:
    """Audio file information"""
    file_path: str
    duration: float  # Duration in seconds
    format: str
    sample_rate: int
    channels: int
    bitrate: Optional[int] = None
    size_bytes: Optional[int] = None


class AudioProcessingError(Exception):
    """Audio processing related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class YouTubeAudioExtractor:
    """Extract audio from YouTube videos using yt-dlp"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize YouTube audio extractor
        
        Args:
            temp_dir: Temporary directory for audio files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_files = []  # Track temp files for cleanup
    
    def extract_audio(self, video_id: str, format: str = "wav", quality: str = "best") -> AudioInfo:
        """
        Extract audio from YouTube video
        
        Function Description: Extract audio from YouTube video using video ID
        Input Parameters: video_id (string), format (string, optional), quality (string, optional)
        Return Parameters: AudioInfo object with file path and metadata
        URL Address: N/A (Utility function)
        Request Method: N/A (Utility function)
        """
        if not video_id or len(video_id) != 11:
            raise AudioProcessingError(f"Invalid YouTube video ID: {video_id}", "INVALID_VIDEO_ID")
        
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        output_path = os.path.join(self.temp_dir, f"{video_id}_audio.{format}")
        
        # yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, f"{video_id}_audio.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }],
            'quiet': True,  # Suppress output
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(youtube_url, download=False)
                if not info:
                    raise AudioProcessingError(f"Could not get video info for: {video_id}", "VIDEO_INFO_ERROR")
                
                # Check if video is available
                if info.get('is_live'):
                    raise AudioProcessingError(f"Live streams not supported: {video_id}", "LIVE_STREAM_NOT_SUPPORTED")
                
                # Download and extract audio
                ydl.download([youtube_url])
                
                # Find the extracted audio file
                if not os.path.exists(output_path):
                    # Try common extensions
                    for ext in ['wav', 'mp3', 'm4a', 'webm']:
                        alt_path = os.path.join(self.temp_dir, f"{video_id}_audio.{ext}")
                        if os.path.exists(alt_path):
                            output_path = alt_path
                            format = ext
                            break
                    else:
                        raise AudioProcessingError(f"Audio file not found after extraction: {video_id}", "AUDIO_FILE_NOT_FOUND")
                
                self.temp_files.append(output_path)
                
                # Get audio information
                audio_info = self._get_audio_info(output_path, format)
                logger.info(f"Successfully extracted audio for video {video_id}: {audio_info.duration:.2f}s")
                
                return audio_info
                
        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error for {video_id}: {e}")
            raise AudioProcessingError(f"Failed to download audio: {str(e)}", "DOWNLOAD_ERROR")
        
        except Exception as e:
            logger.error(f"Unexpected error extracting audio for {video_id}: {e}")
            raise AudioProcessingError(f"Audio extraction failed: {str(e)}", "EXTRACTION_ERROR")
    
    def _get_audio_info(self, file_path: str, format: str) -> AudioInfo:
        """Get audio file information using pydub"""
        try:
            audio = AudioSegment.from_file(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            
            return AudioInfo(
                file_path=file_path,
                duration=len(audio) / 1000.0,  # Convert ms to seconds
                format=format,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                bitrate=audio.frame_rate * audio.sample_width * 8 * audio.channels,
                size_bytes=file_size
            )
        
        except Exception as e:
            logger.error(f"Error getting audio info for {file_path}: {e}")
            # Return basic info if pydub fails
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            return AudioInfo(
                file_path=file_path,
                duration=0.0,  # Unknown duration
                format=format,
                sample_rate=16000,  # Default
                channels=1,  # Default mono
                size_bytes=file_size
            )
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {file_path}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_temp_files()


class AudioPreprocessor:
    """Preprocess audio for optimal STT processing"""
    
    @staticmethod
    def normalize_audio(audio_info: AudioInfo, target_sample_rate: int = 16000) -> AudioInfo:
        """
        Normalize audio for STT processing
        
        Function Description: Normalize audio sample rate and format for STT
        Input Parameters: audio_info (AudioInfo), target_sample_rate (int, optional)
        Return Parameters: AudioInfo object with normalized audio
        URL Address: N/A (Utility function)
        Request Method: N/A (Utility function)
        """
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_info.file_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.debug("Converted audio to mono")
            
            # Resample if needed
            if audio.frame_rate != target_sample_rate:
                audio = audio.set_frame_rate(target_sample_rate)
                logger.debug(f"Resampled audio to {target_sample_rate}Hz")
            
            # Normalize volume
            audio = audio.normalize()
            logger.debug("Normalized audio volume")
            
            # Create new output path
            base_path, ext = os.path.splitext(audio_info.file_path)
            normalized_path = f"{base_path}_normalized{ext}"
            
            # Export normalized audio
            audio.export(normalized_path, format=audio_info.format)
            
            # Create new AudioInfo for normalized file
            return AudioInfo(
                file_path=normalized_path,
                duration=len(audio) / 1000.0,
                format=audio_info.format,
                sample_rate=target_sample_rate,
                channels=1,
                bitrate=target_sample_rate * 16,  # 16-bit
                size_bytes=os.path.getsize(normalized_path)
            )
        
        except Exception as e:
            logger.error(f"Error normalizing audio {audio_info.file_path}: {e}")
            raise AudioProcessingError(f"Audio normalization failed: {str(e)}", "NORMALIZATION_ERROR")
    
    @staticmethod
    def segment_audio(audio_info: AudioInfo, max_duration: float = 600.0) -> list[AudioInfo]:
        """
        Segment long audio files for processing
        
        Function Description: Split long audio into segments for STT processing
        Input Parameters: audio_info (AudioInfo), max_duration (float, optional)
        Return Parameters: List of AudioInfo objects for segments
        URL Address: N/A (Utility function)
        Request Method: N/A (Utility function)
        """
        if audio_info.duration <= max_duration:
            return [audio_info]  # No segmentation needed
        
        try:
            audio = AudioSegment.from_file(audio_info.file_path)
            segments = []
            
            segment_length_ms = int(max_duration * 1000)  # Convert to milliseconds
            base_path, ext = os.path.splitext(audio_info.file_path)
            
            for i, start_ms in enumerate(range(0, len(audio), segment_length_ms)):
                end_ms = min(start_ms + segment_length_ms, len(audio))
                segment = audio[start_ms:end_ms]
                
                segment_path = f"{base_path}_segment_{i:03d}{ext}"
                segment.export(segment_path, format=audio_info.format)
                
                segment_info = AudioInfo(
                    file_path=segment_path,
                    duration=(end_ms - start_ms) / 1000.0,
                    format=audio_info.format,
                    sample_rate=audio_info.sample_rate,
                    channels=audio_info.channels,
                    bitrate=audio_info.bitrate,
                    size_bytes=os.path.getsize(segment_path)
                )
                
                segments.append(segment_info)
                logger.debug(f"Created audio segment {i}: {segment_info.duration:.2f}s")
            
            logger.info(f"Split audio into {len(segments)} segments")
            return segments
        
        except Exception as e:
            logger.error(f"Error segmenting audio {audio_info.file_path}: {e}")
            raise AudioProcessingError(f"Audio segmentation failed: {str(e)}", "SEGMENTATION_ERROR")


def cleanup_audio_file(file_path: str):
    """
    Utility function to clean up a single audio file
    
    Args:
        file_path: Path to audio file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up audio file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up audio file {file_path}: {e}")


def get_supported_audio_formats() -> list[str]:
    """
    Get list of supported audio formats
    
    Returns:
        List of supported audio format extensions
    """
    return ["wav", "mp3", "m4a", "webm", "ogg", "flac"]


def validate_audio_file(file_path: str) -> bool:
    """
    Validate if file is a valid audio file
    
    Args:
        file_path: Path to audio file
        
    Returns:
        True if valid audio file, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        # Try to load with pydub
        audio = AudioSegment.from_file(file_path)
        return len(audio) > 0  # Has some duration
    except Exception:
        return False