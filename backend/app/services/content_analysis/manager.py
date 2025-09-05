"""
Content Analysis Manager - Orchestrates the mind map generation pipeline
"""

import os
import logging
import time
from typing import Optional, Dict, Any

from .base import AnalysisConfig, ContentType, MindMapStructure, ContentAnalysisError
from .analyzer import ContentAnalyzer
from .mock_analyzer import MockContentAnalyzer
from app.services.stt_services.base import TranscriptResult
from app.models.mindmap_node import MindMapNode
from app.core.database import get_session

logger = logging.getLogger(__name__)


class ContentAnalysisManager:
    """Manages content analysis and mind map generation"""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock or os.getenv('USE_MOCK_ANALYSIS', '').lower() == 'true'
        self._analyzer = None
        logger.info(f"Content Analysis Manager initialized (mock={self.use_mock})")
    
    def get_analyzer(self, config: AnalysisConfig) -> ContentAnalyzer:
        """Get content analyzer instance"""
        if self.use_mock:
            return MockContentAnalyzer(config)
        else:
            return ContentAnalyzer(config)
    
    def generate_mind_map(
        self, 
        transcript: TranscriptResult, 
        config: Optional[AnalysisConfig] = None
    ) -> MindMapStructure:
        """
        Generate mind map structure from transcript
        
        Args:
            transcript: STT transcript result
            config: Analysis configuration (optional)
            
        Returns:
            MindMapStructure with hierarchical nodes
        """
        if config is None:
            config = self._create_default_config(transcript)
        
        analyzer = self.get_analyzer(config)
        
        logger.info(f"Generating mind map for video: {transcript.video_id}")
        start_time = time.time()
        
        try:
            # Generate mind map structure
            mind_map = analyzer.analyze_transcript(transcript)
            
            processing_time = time.time() - start_time
            logger.info(f"Mind map generation completed in {processing_time:.2f}s")
            
            return mind_map
            
        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            raise ContentAnalysisError(f"Mind map generation failed: {str(e)}")
    
    def save_mind_map(self, mind_map: MindMapStructure) -> Dict[str, Any]:
        """
        Save mind map structure to database
        
        Args:
            mind_map: Generated mind map structure
            
        Returns:
            Dictionary with save results
        """
        logger.info(f"Saving mind map for video: {mind_map.video_id}")
        
        try:
            with get_session() as session:
                # Clear existing nodes for this video
                existing_nodes = session.query(MindMapNode).filter(
                    MindMapNode.video_id == mind_map.video_id
                ).all()
                
                if existing_nodes:
                    logger.info(f"Removing {len(existing_nodes)} existing nodes")
                    for node in existing_nodes:
                        session.delete(node)
                    session.flush()
                
                # Create new nodes
                created_nodes = []
                node_id_mapping = {}  # Map from structure IDs to database IDs
                
                # First pass: create all nodes
                for node_data in mind_map.nodes:
                    db_node = MindMapNode(
                        video_id=mind_map.video_id,
                        parent_node_id=None,  # Will be set in second pass
                        content=node_data.content,
                        summary=node_data.summary,
                        timestamp_start=node_data.timestamp_start,
                        timestamp_end=node_data.timestamp_end,
                        node_type=node_data.node_type.value,
                        depth=node_data.depth,
                        keywords=node_data.keywords,
                        position_x=node_data.position_x,
                        position_y=node_data.position_y,
                        confidence=node_data.confidence,
                        importance=node_data.importance,
                        word_count=node_data.word_count,
                        display_order=0,  # Will be set based on position
                        analysis_metadata={
                            "analysis_version": "1.0.0",
                            "content_type": mind_map.content_type.value,
                            "confidence_score": mind_map.confidence_score
                        }
                    )
                    
                    session.add(db_node)
                    session.flush()  # Get the database ID
                    
                    node_id_mapping[node_data.id] = db_node.id
                    created_nodes.append(db_node)
                
                # Second pass: set parent relationships
                for i, node_data in enumerate(mind_map.nodes):
                    db_node = created_nodes[i]
                    if node_data.parent_node_id:
                        db_node.parent_node_id = node_id_mapping.get(node_data.parent_node_id)
                
                session.commit()
                
                logger.info(f"Saved {len(created_nodes)} mind map nodes to database")
                
                return {
                    "success": True,
                    "nodes_created": len(created_nodes),
                    "video_id": mind_map.video_id,
                    "processing_time": mind_map.processing_time,
                    "confidence_score": mind_map.confidence_score
                }
                
        except Exception as e:
            logger.error(f"Failed to save mind map: {e}")
            raise ContentAnalysisError(f"Failed to save mind map: {str(e)}")
    
    def get_mind_map(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get existing mind map for video
        
        Args:
            video_id: Video ID
            
        Returns:
            Mind map data or None if not found
        """
        try:
            with get_session() as session:
                nodes = MindMapNode.get_by_video_id(session, video_id)
                
                if not nodes:
                    return None
                
                # Convert to dictionary format
                nodes_data = [node.to_dict() for node in nodes]
                
                # Calculate statistics
                root_nodes = [n for n in nodes_data if n["node_type"] == "root"]
                max_depth = max((n["depth"] for n in nodes_data), default=0)
                
                return {
                    "video_id": video_id,
                    "nodes": nodes_data,
                    "statistics": {
                        "total_nodes": len(nodes_data),
                        "root_nodes": len(root_nodes),
                        "max_depth": max_depth,
                        "node_types": self._count_node_types(nodes_data)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get mind map: {e}")
            return None
    
    def delete_mind_map(self, video_id: str) -> bool:
        """
        Delete mind map for video
        
        Args:
            video_id: Video ID
            
        Returns:
            True if successful
        """
        try:
            with get_session() as session:
                nodes = session.query(MindMapNode).filter(
                    MindMapNode.video_id == video_id
                ).all()
                
                if nodes:
                    for node in nodes:
                        session.delete(node)
                    session.commit()
                    logger.info(f"Deleted {len(nodes)} nodes for video: {video_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete mind map: {e}")
            return False
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """Get content analysis service status"""
        return {
            "service_name": "Content Analysis Manager",
            "using_mock": self.use_mock,
            "analyzer_type": "MockContentAnalyzer" if self.use_mock else "ContentAnalyzer",
            "features": {
                "topic_extraction": True,
                "content_summarization": True,
                "keyword_extraction": True,
                "hierarchical_structure": True,
                "timestamp_mapping": True,
                "position_calculation": True
            },
            "supported_content_types": [ct.value for ct in ContentType],
            "max_depth": 10,
            "version": "1.0.0"
        }
    
    def _create_default_config(self, transcript: TranscriptResult) -> AnalysisConfig:
        """Create default analysis configuration based on transcript"""
        # Detect content type based on duration and language
        content_type = ContentType.EDUCATIONAL  # Default
        
        if transcript.duration < 300:  # Less than 5 minutes
            content_type = ContentType.TUTORIAL
        elif transcript.duration > 3600:  # More than 1 hour
            content_type = ContentType.DISCUSSION
        
        return AnalysisConfig(
            max_depth=4,
            min_segment_duration=10.0,
            max_segment_duration=300.0,
            content_type=content_type,
            language=transcript.language or "en",
            use_llm=False,  # Disable LLM for now
            confidence_threshold=0.6,
            importance_threshold=0.4
        )
    
    def _count_node_types(self, nodes_data: list) -> Dict[str, int]:
        """Count nodes by type"""
        type_counts = {}
        for node in nodes_data:
            node_type = node["node_type"]
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
    
    def estimate_processing_time(self, transcript: TranscriptResult) -> float:
        """
        Estimate processing time for transcript analysis
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            Estimated processing time in seconds
        """
        # Base time calculation
        segment_count = len(transcript.segments)
        duration_minutes = transcript.duration / 60.0
        
        if self.use_mock:
            # Mock processing is very fast
            return min(segment_count * 0.1 + duration_minutes * 0.2, 5.0)
        else:
            # Real processing time estimation
            return min(segment_count * 0.5 + duration_minutes * 1.0, 60.0)