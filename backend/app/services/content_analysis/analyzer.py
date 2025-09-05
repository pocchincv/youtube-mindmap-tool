"""
Content Analysis Pipeline Implementation
"""

import time
import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

from .base import (
    BaseContentAnalyzer, 
    AnalysisConfig, 
    ContentSegment, 
    TopicHierarchy, 
    MindMapStructure, 
    MindMapNodeData,
    NodeType, 
    ContentType,
    ContentAnalysisError
)
from app.services.stt_services.base import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class ContentAnalyzer(BaseContentAnalyzer):
    """Main content analyzer implementation"""
    
    def __init__(self, config: AnalysisConfig):
        super().__init__(config)
        self.validate_config()
        
        # Initialize NLP tools if available
        self._init_nlp_tools()
    
    def _init_nlp_tools(self):
        """Initialize NLP processing tools"""
        try:
            import nltk
            # Download required NLTK data
            self._ensure_nltk_data()
            self.has_nltk = True
            logger.info("NLTK initialized successfully")
        except ImportError:
            self.has_nltk = False
            logger.warning("NLTK not available, using basic text processing")
        
        # Initialize other NLP libraries as needed
        self.stop_words = self._get_stop_words()
    
    def _ensure_nltk_data(self):
        """Ensure required NLTK data is downloaded"""
        import nltk
        required_datasets = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
        
        for dataset in required_datasets:
            try:
                nltk.data.find(f'tokenizers/{dataset}')
            except LookupError:
                try:
                    nltk.download(dataset, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download NLTK dataset {dataset}: {e}")
    
    def _get_stop_words(self) -> set:
        """Get stop words for text processing"""
        if self.has_nltk:
            try:
                import nltk
                return set(nltk.corpus.stopwords.words('english'))
            except:
                pass
        
        # Fallback basic stop words
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'you', 'your', 'this', 'they',
            'we', 'can', 'could', 'should', 'would', 'have', 'had', 'do', 'does',
            'did', 'going', 'so', 'now', 'well', 'like', 'just', 'get', 'got'
        }
    
    def analyze_transcript(self, transcript: TranscriptResult) -> MindMapStructure:
        """
        Analyze transcript and generate mind map structure
        """
        logger.info(f"Starting content analysis for video: {transcript.video_id}")
        start_time = time.time()
        
        try:
            # Step 1: Preprocess transcript segments
            segments = self._preprocess_segments(transcript.segments)
            logger.info(f"Preprocessed {len(segments)} transcript segments")
            
            # Step 2: Create content segments with analysis
            content_segments = self._create_content_segments(segments)
            logger.info(f"Created {len(content_segments)} content segments")
            
            # Step 3: Extract topic hierarchy
            topic_hierarchy = self._extract_topic_hierarchy(content_segments)
            logger.info(f"Extracted topic hierarchy with {len(topic_hierarchy)} main topics")
            
            # Step 4: Build mind map structure
            nodes = self._build_mind_map_nodes(
                transcript.video_id, 
                content_segments, 
                topic_hierarchy
            )
            logger.info(f"Built mind map with {len(nodes)} nodes")
            
            # Step 5: Calculate positions for visualization
            self._calculate_node_positions(nodes)
            
            processing_time = time.time() - start_time
            confidence_score = self._calculate_overall_confidence(nodes)
            
            # Create final mind map structure
            mind_map = MindMapStructure(
                video_id=transcript.video_id,
                nodes=nodes,
                content_type=self.config.content_type,
                analysis_metadata={
                    "segments_count": len(content_segments),
                    "topics_count": len(topic_hierarchy),
                    "nodes_count": len(nodes),
                    "max_depth": max((node.depth for node in nodes), default=0),
                    "language": transcript.language,
                    "analyzer_version": "1.0.0"
                },
                total_duration=transcript.duration,
                processing_time=processing_time,
                confidence_score=confidence_score
            )
            
            logger.info(f"Content analysis completed in {processing_time:.2f}s")
            return mind_map
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            raise ContentAnalysisError(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")
    
    def _preprocess_segments(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Preprocess and filter transcript segments"""
        processed_segments = []
        
        for segment in segments:
            # Clean text
            cleaned_text = self._clean_text(segment.text)
            
            # Skip very short segments
            if len(cleaned_text.strip()) < 10:
                continue
            
            # Update segment with cleaned text
            segment.text = cleaned_text
            processed_segments.append(segment)
        
        return processed_segments
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove filler words and sounds
        filler_patterns = [
            r'\b(um|uh|ah|er|hmm|eh)\b',
            r'\b(you know|like|basically|actually)\b',
            r'\[.*?\]',  # Remove bracketed content
            r'\(.*?\)',  # Remove parenthetical content
        ]
        
        for pattern in filler_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _create_content_segments(self, segments: List[TranscriptSegment]) -> List[ContentSegment]:
        """Create analyzed content segments"""
        content_segments = []
        
        for i, segment in enumerate(segments):
            # Extract topics and keywords
            topics = self.extract_topics(segment.text)
            keywords = self.extract_keywords(segment.text)
            
            # Generate summary
            summary = self.generate_summary(segment.text)
            
            # Calculate metrics
            word_count = len(segment.text.split())
            confidence = segment.confidence or 0.8
            
            content_segment = ContentSegment(
                id=f"seg_{i}",
                content=segment.text,
                timestamp_start=segment.start_time,
                timestamp_end=segment.end_time,
                topics=topics,
                keywords=keywords,
                summary=summary,
                importance=0.5,  # Will be calculated later
                confidence=confidence,
                word_count=word_count
            )
            
            # Calculate importance
            content_segment.importance = self.calculate_importance(content_segment)
            content_segments.append(content_segment)
        
        return content_segments
    
    def extract_topics(self, content: str) -> List[str]:
        """Extract main topics from content using keyword analysis"""
        # Tokenize and clean
        words = self._tokenize(content.lower())
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Use POS tagging if available
        if self.has_nltk:
            try:
                import nltk
                pos_tags = nltk.pos_tag(words)
                # Extract nouns and noun phrases as potential topics
                topics = [word for word, pos in pos_tags if pos.startswith('N')]
            except:
                topics = words
        else:
            topics = words
        
        # Get most frequent potential topics
        topic_counts = Counter(topics)
        main_topics = [topic for topic, count in topic_counts.most_common(5)]
        
        return main_topics
    
    def generate_summary(self, content: str, max_length: int = 100) -> str:
        """Generate summary for content"""
        # Simple extractive summarization
        sentences = self._split_sentences(content)
        
        if not sentences:
            return content[:max_length] + "..."
        
        if len(sentences) == 1:
            return sentences[0][:max_length] + "..." if len(sentences[0]) > max_length else sentences[0]
        
        # Score sentences by word frequency and position
        word_freq = self._get_word_frequencies(content)
        sentence_scores = []
        
        for i, sentence in enumerate(sentences):
            words = self._tokenize(sentence.lower())
            score = sum(word_freq.get(word, 0) for word in words if word not in self.stop_words)
            # Boost score for early sentences
            position_boost = 1.0 - (i / len(sentences)) * 0.3
            sentence_scores.append((score * position_boost, sentence))
        
        # Get best sentence
        if sentence_scores:
            best_sentence = max(sentence_scores, key=lambda x: x[0])[1]
            return best_sentence[:max_length] + "..." if len(best_sentence) > max_length else best_sentence
        
        return content[:max_length] + "..."
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content"""
        words = self._tokenize(content.lower())
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Filter out common words and very long words
        words = [word for word in words if len(word) < 20 and word.isalpha()]
        
        # Get most frequent words as keywords
        word_counts = Counter(words)
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
    
    def _extract_topic_hierarchy(self, segments: List[ContentSegment]) -> List[TopicHierarchy]:
        """Extract hierarchical topic structure"""
        # Collect all topics from segments
        all_topics = []
        topic_segments = {}
        
        for segment in segments:
            for topic in segment.topics:
                all_topics.append(topic)
                if topic not in topic_segments:
                    topic_segments[topic] = []
                topic_segments[topic].append(segment.id)
        
        # Find main topics (most frequent)
        topic_counts = Counter(all_topics)
        main_topics = topic_counts.most_common(10)
        
        hierarchies = []
        for topic, count in main_topics:
            # Get segments for this topic
            related_segments = topic_segments.get(topic, [])
            
            # Calculate confidence based on frequency and segment importance
            confidence = min(count / len(segments), 1.0)
            importance = sum(
                seg.importance for seg in segments 
                if seg.id in related_segments
            ) / max(len(related_segments), 1)
            
            # Extract keywords from topic-related content
            topic_content = " ".join([
                seg.content for seg in segments 
                if seg.id in related_segments
            ])
            keywords = self.extract_keywords(topic_content, 5)
            
            hierarchy = TopicHierarchy(
                topic=topic,
                confidence=confidence,
                importance=importance,
                keywords=keywords,
                subtopics=[],
                segments=related_segments
            )
            hierarchies.append(hierarchy)
        
        return hierarchies
    
    def _build_mind_map_nodes(
        self, 
        video_id: str, 
        segments: List[ContentSegment], 
        hierarchies: List[TopicHierarchy]
    ) -> List[MindMapNodeData]:
        """Build hierarchical mind map nodes"""
        nodes = []
        node_index = 0
        
        # Create root node
        root_content = f"Content analysis for video {video_id}"
        root_summary = f"Mind map overview with {len(hierarchies)} main topics"
        
        root_node = MindMapNodeData(
            id=self.generate_node_id(video_id, node_index),
            video_id=video_id,
            parent_node_id=None,
            content=root_content,
            summary=root_summary,
            timestamp_start=0.0,
            timestamp_end=max((seg.timestamp_end for seg in segments), default=0.0),
            node_type=NodeType.ROOT,
            depth=0,
            keywords=["overview", "analysis", "mindmap"],
            confidence=0.9,
            importance=1.0,
            word_count=len(root_content.split())
        )
        nodes.append(root_node)
        node_index += 1
        
        # Create topic nodes
        for hierarchy in hierarchies:
            # Create main topic node
            topic_segments = [seg for seg in segments if seg.id in hierarchy.segments]
            topic_content = " ".join([seg.content for seg in topic_segments])
            topic_summary = self.generate_summary(topic_content, 200)
            
            topic_node = MindMapNodeData(
                id=self.generate_node_id(video_id, node_index),
                video_id=video_id,
                parent_node_id=root_node.id,
                content=topic_content,
                summary=topic_summary,
                timestamp_start=min((seg.timestamp_start for seg in topic_segments), default=0.0),
                timestamp_end=max((seg.timestamp_end for seg in topic_segments), default=0.0),
                node_type=NodeType.TOPIC,
                depth=1,
                keywords=hierarchy.keywords,
                confidence=hierarchy.confidence,
                importance=hierarchy.importance,
                word_count=sum(seg.word_count for seg in topic_segments)
            )
            nodes.append(topic_node)
            root_node.children.append(topic_node.id)
            node_index += 1
            
            # Create detail nodes from segments
            for segment in topic_segments:
                if segment.importance > self.config.importance_threshold:
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
    
    def _calculate_node_positions(self, nodes: List[MindMapNodeData]):
        """Calculate positions for mind map visualization"""
        # Simple tree layout algorithm
        nodes_by_depth = {}
        for node in nodes:
            if node.depth not in nodes_by_depth:
                nodes_by_depth[node.depth] = []
            nodes_by_depth[node.depth].append(node)
        
        # Position nodes
        for depth, depth_nodes in nodes_by_depth.items():
            y_base = depth * 200  # Vertical spacing between levels
            x_spacing = 800 / max(len(depth_nodes), 1)  # Horizontal spacing
            
            for i, node in enumerate(depth_nodes):
                node.position_x = i * x_spacing + x_spacing / 2
                node.position_y = y_base
    
    def _calculate_overall_confidence(self, nodes: List[MindMapNodeData]) -> float:
        """Calculate overall analysis confidence"""
        confidences = [node.confidence for node in nodes if node.confidence is not None]
        return sum(confidences) / len(confidences) if confidences else 0.7
    
    # Helper methods
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if self.has_nltk:
            try:
                import nltk
                return nltk.word_tokenize(text)
            except:
                pass
        
        # Fallback tokenization
        return re.findall(r'\b\w+\b', text.lower())
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if self.has_nltk:
            try:
                import nltk
                return nltk.sent_tokenize(text)
            except:
                pass
        
        # Fallback sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_word_frequencies(self, text: str) -> Dict[str, float]:
        """Get word frequency scores"""
        words = self._tokenize(text.lower())
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        word_counts = Counter(words)
        max_count = max(word_counts.values()) if word_counts else 1
        
        # Normalize frequencies
        word_freq = {word: count / max_count for word, count in word_counts.items()}
        return word_freq