"""
Mock Content Analyzer for development and testing
"""

import time
import random
import logging
from typing import List, Dict, Any

from .base import (
    BaseContentAnalyzer, 
    AnalysisConfig, 
    ContentSegment, 
    TopicHierarchy, 
    MindMapStructure, 
    MindMapNodeData,
    NodeType, 
    ContentType
)
from app.services.stt_services.base import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class MockContentAnalyzer(BaseContentAnalyzer):
    """Mock content analyzer for development and testing"""
    
    def __init__(self, config: AnalysisConfig):
        super().__init__(config)
        
        # Sample data for different content types
        self.sample_topics = {
            ContentType.EDUCATIONAL: [
                "Introduction", "Basic Concepts", "Key Principles", "Examples", 
                "Applications", "Case Studies", "Summary", "Next Steps"
            ],
            ContentType.TUTORIAL: [
                "Getting Started", "Setup", "Step 1", "Step 2", "Step 3", 
                "Troubleshooting", "Tips and Tricks", "Conclusion"
            ],
            ContentType.ENTERTAINMENT: [
                "Opening", "Main Topic", "Discussion", "Reactions", 
                "Commentary", "Highlights", "Wrap Up"
            ],
            ContentType.NEWS: [
                "Headlines", "Breaking News", "Analysis", "Expert Opinion", 
                "Background", "Impact", "Updates", "Summary"
            ],
            ContentType.DISCUSSION: [
                "Introduction", "Main Arguments", "Counterpoints", "Evidence", 
                "Examples", "Debate", "Conclusions", "Q&A"
            ],
            ContentType.REVIEW: [
                "Overview", "Features", "Pros", "Cons", "Performance", 
                "Comparison", "Verdict", "Recommendation"
            ]
        }
        
        self.sample_keywords = {
            ContentType.EDUCATIONAL: [
                "learn", "understand", "concept", "principle", "theory", "practice",
                "example", "important", "remember", "key", "fundamental"
            ],
            ContentType.TUTORIAL: [
                "step", "follow", "click", "install", "setup", "configure",
                "run", "execute", "complete", "finish", "done"
            ],
            ContentType.ENTERTAINMENT: [
                "funny", "amazing", "incredible", "awesome", "interesting",
                "story", "experience", "reaction", "opinion", "think"
            ]
        }
        
        logger.info(f"Mock content analyzer initialized for {config.content_type.value}")
    
    def analyze_transcript(self, transcript: TranscriptResult) -> MindMapStructure:
        """Generate mock mind map structure"""
        logger.info(f"Mock analyzing transcript for video: {transcript.video_id}")
        
        # Simulate processing time
        start_time = time.time()
        time.sleep(0.5)  # Mock processing delay
        
        # Generate mock content segments
        content_segments = self._create_mock_content_segments(transcript.segments)
        
        # Generate mock topic hierarchy
        topic_hierarchy = self._create_mock_topic_hierarchy(content_segments)
        
        # Build mock mind map nodes
        nodes = self._build_mock_mind_map_nodes(
            transcript.video_id, 
            content_segments, 
            topic_hierarchy
        )
        
        # Calculate positions
        self._calculate_node_positions(nodes)
        
        processing_time = time.time() - start_time
        
        mind_map = MindMapStructure(
            video_id=transcript.video_id,
            nodes=nodes,
            content_type=self.config.content_type,
            analysis_metadata={
                "mock": True,
                "segments_count": len(content_segments),
                "topics_count": len(topic_hierarchy),
                "nodes_count": len(nodes),
                "max_depth": max((node.depth for node in nodes), default=0),
                "language": transcript.language or "en",
                "analyzer_version": "mock-1.0.0"
            },
            total_duration=transcript.duration,
            processing_time=processing_time,
            confidence_score=random.uniform(0.75, 0.95)
        )
        
        logger.info(f"Mock analysis completed: {len(nodes)} nodes generated")
        return mind_map
    
    def _create_mock_content_segments(self, transcript_segments: List[TranscriptSegment]) -> List[ContentSegment]:
        """Create mock analyzed content segments"""
        content_segments = []
        
        for i, segment in enumerate(transcript_segments):
            # Generate mock topics and keywords
            topics = self.extract_topics(segment.text)
            keywords = self.extract_keywords(segment.text)
            
            # Generate mock summary
            summary = self.generate_summary(segment.text)
            
            # Mock metrics
            word_count = len(segment.text.split())
            confidence = random.uniform(0.7, 0.95)
            importance = random.uniform(0.3, 0.9)
            
            content_segment = ContentSegment(
                id=f"mock_seg_{i}",
                content=segment.text,
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                topics=topics,
                keywords=keywords,
                summary=summary,
                importance=importance,
                confidence=confidence,
                word_count=word_count
            )
            
            content_segments.append(content_segment)
        
        return content_segments
    
    def _create_mock_topic_hierarchy(self, segments: List[ContentSegment]) -> List[TopicHierarchy]:
        """Create mock topic hierarchy"""
        sample_topics = self.sample_topics.get(self.config.content_type, 
                                              self.sample_topics[ContentType.EDUCATIONAL])
        
        # Select random topics based on content length
        num_topics = min(len(sample_topics), max(3, len(segments) // 5))
        selected_topics = random.sample(sample_topics, num_topics)
        
        hierarchies = []
        segment_groups = self._group_segments_by_time(segments, num_topics)
        
        for i, topic in enumerate(selected_topics):
            # Assign segments to this topic
            topic_segments = segment_groups[i] if i < len(segment_groups) else []
            
            # Mock values
            confidence = random.uniform(0.6, 0.9)
            importance = random.uniform(0.5, 0.8)
            keywords = random.sample(
                self.sample_keywords.get(self.config.content_type, 
                                       self.sample_keywords[ContentType.EDUCATIONAL]),
                min(5, len(self.sample_keywords.get(self.config.content_type, [])))
            )
            
            hierarchy = TopicHierarchy(
                topic=topic,
                confidence=confidence,
                importance=importance,
                keywords=keywords,
                subtopics=[],
                segments=[seg.id for seg in topic_segments]
            )
            hierarchies.append(hierarchy)
        
        return hierarchies
    
    def _group_segments_by_time(self, segments: List[ContentSegment], num_groups: int) -> List[List[ContentSegment]]:
        """Group segments by time for topic assignment"""
        if not segments:
            return []
        
        segments_per_group = len(segments) // num_groups
        groups = []
        
        for i in range(num_groups):
            start_idx = i * segments_per_group
            end_idx = start_idx + segments_per_group if i < num_groups - 1 else len(segments)
            groups.append(segments[start_idx:end_idx])
        
        return groups
    
    def _build_mock_mind_map_nodes(
        self, 
        video_id: str, 
        segments: List[ContentSegment], 
        hierarchies: List[TopicHierarchy]
    ) -> List[MindMapNodeData]:
        """Build mock hierarchical mind map nodes"""
        nodes = []
        node_index = 0
        
        # Create root node
        root_node = MindMapNodeData(
            id=self.generate_node_id(video_id, node_index),
            video_id=video_id,
            parent_node_id=None,
            content=f"Mock analysis for {self.config.content_type.value} content",
            summary=f"Comprehensive mind map with {len(hierarchies)} main topics covering various aspects of the video content.",
            timestamp_start=0.0,
            timestamp_end=max((seg.timestamp_end for seg in segments), default=600.0),
            node_type=NodeType.ROOT,
            depth=0,
            keywords=["overview", "analysis", "mindmap", self.config.content_type.value],
            confidence=0.9,
            importance=1.0,
            word_count=100
        )
        nodes.append(root_node)
        node_index += 1
        
        # Create topic nodes
        for hierarchy in hierarchies:
            topic_segments = [seg for seg in segments if seg.id in hierarchy.segments]
            
            # Combine content from segments
            topic_content = " ".join([seg.content for seg in topic_segments])
            if not topic_content:
                topic_content = f"Content related to {hierarchy.topic} - detailed discussion and examples."
            
            topic_summary = self.generate_summary(topic_content, 150)
            
            topic_node = MindMapNodeData(
                id=self.generate_node_id(video_id, node_index),
                video_id=video_id,
                parent_node_id=root_node.id,
                content=topic_content,
                summary=topic_summary,
                timestamp_start=min((seg.timestamp_start for seg in topic_segments), default=0.0),
                timestamp_end=max((seg.timestamp_end for seg in topic_segments), default=60.0),
                node_type=NodeType.TOPIC,
                depth=1,
                keywords=hierarchy.keywords,
                confidence=hierarchy.confidence,
                importance=hierarchy.importance,
                word_count=len(topic_content.split())
            )
            nodes.append(topic_node)
            root_node.children.append(topic_node.id)
            node_index += 1
            
            # Create subtopic/detail nodes
            important_segments = [seg for seg in topic_segments if seg.importance > 0.6]
            
            for segment in important_segments[:3]:  # Limit to 3 detail nodes per topic
                detail_node = MindMapNodeData(
                    id=self.generate_node_id(video_id, node_index),
                    video_id=video_id,
                    parent_node_id=topic_node.id,
                    content=segment.content,
                    summary=segment.summary,
                    timestamp_start=segment.timestamp_start,
                    timestamp_end=segment.timestamp_end,
                    node_type=NodeType.DETAIL,
                    depth=2,
                    keywords=segment.keywords,
                    confidence=segment.confidence,
                    importance=segment.importance,
                    word_count=segment.word_count
                )
                nodes.append(detail_node)
                topic_node.children.append(detail_node.id)
                node_index += 1
        
        return nodes
    
    def extract_topics(self, content: str) -> List[str]:
        """Extract mock topics from content"""
        # Simple word-based topic extraction for mock
        words = content.lower().split()
        
        # Filter meaningful words (basic approach)
        meaningful_words = [
            word for word in words 
            if len(word) > 4 and word.isalpha()
        ]
        
        # Return sample of words as "topics"
        return meaningful_words[:3] if meaningful_words else ["general", "content", "topic"]
    
    def generate_summary(self, content: str, max_length: int = 100) -> str:
        """Generate mock summary"""
        if len(content) <= max_length:
            return content
        
        # Simple extractive summary - take first sentence or portion
        sentences = content.split('. ')
        if sentences:
            summary = sentences[0]
            if len(summary) > max_length:
                summary = summary[:max_length - 3] + "..."
            return summary
        
        return content[:max_length - 3] + "..."
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract mock keywords"""
        words = content.lower().split()
        
        # Filter words
        keywords = [
            word.strip('.,!?;:') for word in words
            if len(word) > 3 and word.isalpha()
        ]
        
        # Remove duplicates and limit
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:max_keywords]
    
    def _calculate_node_positions(self, nodes: List[MindMapNodeData]):
        """Calculate positions for mock visualization"""
        # Group nodes by depth
        nodes_by_depth = {}
        for node in nodes:
            if node.depth not in nodes_by_depth:
                nodes_by_depth[node.depth] = []
            nodes_by_depth[node.depth].append(node)
        
        # Position nodes in a tree layout
        for depth, depth_nodes in nodes_by_depth.items():
            y_position = depth * 150 + 50  # Vertical spacing
            
            if depth == 0:
                # Root node - center position
                depth_nodes[0].position_x = 400
                depth_nodes[0].position_y = y_position
            else:
                # Distribute nodes horizontally
                total_width = 800
                node_spacing = total_width / (len(depth_nodes) + 1)
                
                for i, node in enumerate(depth_nodes):
                    node.position_x = (i + 1) * node_spacing
                    node.position_y = y_position