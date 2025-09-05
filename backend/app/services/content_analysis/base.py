"""
Base classes for content analysis and mind map generation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from app.services.stt_services.base import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Mind map node types"""
    ROOT = "root"
    TOPIC = "topic"
    SUBTOPIC = "subtopic"
    DETAIL = "detail"


class ContentType(Enum):
    """Content types for different analysis approaches"""
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    TUTORIAL = "tutorial"
    DISCUSSION = "discussion"
    REVIEW = "review"


@dataclass
class AnalysisConfig:
    """Configuration for content analysis"""
    max_depth: int = 4
    min_segment_duration: float = 10.0
    max_segment_duration: float = 300.0
    content_type: ContentType = ContentType.EDUCATIONAL
    language: str = "en"
    use_llm: bool = True
    llm_model: str = "gpt-3.5-turbo"
    confidence_threshold: float = 0.7
    importance_threshold: float = 0.5


@dataclass
class MindMapNodeData:
    """Data structure for mind map node before database storage"""
    id: str
    video_id: str
    parent_node_id: Optional[str]
    content: str
    summary: str
    timestamp_start: float
    timestamp_end: float
    node_type: NodeType
    depth: int
    keywords: List[str]
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    confidence: Optional[float] = None
    importance: Optional[float] = None
    word_count: Optional[int] = None
    children: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class ContentSegment:
    """Analyzed content segment"""
    id: str
    content: str
    timestamp_start: float
    timestamp_end: float
    topics: List[str]
    keywords: List[str]
    summary: str
    importance: float
    confidence: float
    word_count: int


@dataclass
class TopicHierarchy:
    """Topic hierarchy structure"""
    topic: str
    confidence: float
    importance: float
    keywords: List[str]
    subtopics: List["TopicHierarchy"]
    segments: List[str]  # Content segment IDs
    
    def __post_init__(self):
        if self.subtopics is None:
            self.subtopics = []
        if self.segments is None:
            self.segments = []


@dataclass
class MindMapStructure:
    """Complete mind map structure"""
    video_id: str
    nodes: List[MindMapNodeData]
    content_type: ContentType
    analysis_metadata: Dict[str, Any]
    total_duration: float
    processing_time: float
    confidence_score: float
    
    def get_root_nodes(self) -> List[MindMapNodeData]:
        """Get root nodes"""
        return [node for node in self.nodes if node.node_type == NodeType.ROOT]
    
    def get_nodes_by_depth(self, depth: int) -> List[MindMapNodeData]:
        """Get nodes at specific depth"""
        return [node for node in self.nodes if node.depth == depth]
    
    def get_children(self, parent_id: str) -> List[MindMapNodeData]:
        """Get child nodes of a parent"""
        return [node for node in self.nodes if node.parent_node_id == parent_id]


class ContentAnalysisError(Exception):
    """Content analysis related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class BaseContentAnalyzer(ABC):
    """Base class for content analyzers"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze_transcript(self, transcript: TranscriptResult) -> MindMapStructure:
        """
        Analyze transcript and generate mind map structure
        
        Args:
            transcript: Transcript result from STT service
            
        Returns:
            MindMapStructure with hierarchical nodes
            
        Raises:
            ContentAnalysisError: If analysis fails
        """
        pass
    
    @abstractmethod
    def extract_topics(self, content: str) -> List[str]:
        """
        Extract main topics from content
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of extracted topics
        """
        pass
    
    @abstractmethod
    def generate_summary(self, content: str, max_length: int = 100) -> str:
        """
        Generate summary for content
        
        Args:
            content: Text content to summarize
            max_length: Maximum summary length
            
        Returns:
            Generated summary
        """
        pass
    
    @abstractmethod
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from content
        
        Args:
            content: Text content to analyze
            max_keywords: Maximum number of keywords
            
        Returns:
            List of extracted keywords
        """
        pass
    
    def validate_config(self) -> bool:
        """Validate analysis configuration"""
        if self.config.max_depth < 1 or self.config.max_depth > 10:
            raise ContentAnalysisError("Invalid max_depth: must be between 1 and 10")
        
        if self.config.min_segment_duration <= 0:
            raise ContentAnalysisError("Invalid min_segment_duration: must be positive")
        
        if self.config.confidence_threshold < 0 or self.config.confidence_threshold > 1:
            raise ContentAnalysisError("Invalid confidence_threshold: must be between 0 and 1")
        
        return True
    
    def calculate_importance(self, segment: ContentSegment) -> float:
        """Calculate importance score for content segment"""
        # Base importance calculation
        word_count_factor = min(segment.word_count / 100.0, 1.0)
        confidence_factor = segment.confidence
        duration_factor = min((segment.timestamp_end - segment.timestamp_start) / 60.0, 1.0)
        
        # Weighted average
        importance = (
            word_count_factor * 0.3 +
            confidence_factor * 0.4 +
            duration_factor * 0.3
        )
        
        return min(importance, 1.0)
    
    def generate_node_id(self, video_id: str, index: int) -> str:
        """Generate unique node ID"""
        import uuid
        return f"{video_id}_{index}_{str(uuid.uuid4())[:8]}"