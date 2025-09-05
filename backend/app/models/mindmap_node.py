"""
MindMap Node model for storing hierarchical mind map structure and content analysis
"""

from sqlalchemy import String, ForeignKey, Integer, Float, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List

from .base import Base, UUIDMixin, TimestampMixin


class MindMapNode(Base, UUIDMixin, TimestampMixin):
    """Mind map node with hierarchical structure, content analysis, and video timestamps"""
    
    __tablename__ = "mindmap_nodes"
    
    # Foreign key to video
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("videos.id"),
        nullable=False,
        index=True
    )
    
    # Self-referencing foreign key for parent node (hierarchical structure)
    parent_node_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("mindmap_nodes.id"),
        nullable=True,
        index=True
    )
    
    # Node content and summary
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    # Video timestamps for this node (in seconds, with decimals for precision)
    timestamp_start: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    timestamp_end: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    # Node type classification based on Issue #5 requirements
    node_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="detail"
    )  # root, topic, subtopic, detail
    
    # Node hierarchy depth (root = 0)
    depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Keywords extracted from content
    keywords: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    # Position coordinates for visualization
    position_x: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    position_y: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Analysis quality metrics
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )  # Analysis confidence score (0-1)
    
    importance: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )  # Content importance score (0-1)
    
    word_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # Display order among siblings
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Additional analysis metadata
    analysis_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Relationships
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="mindmap_nodes"
    )
    
    # Self-referencing relationship for parent-child structure
    parent_node: Mapped[Optional["MindMapNode"]] = relationship(
        "MindMapNode",
        remote_side="MindMapNode.id",
        back_populates="child_nodes"
    )
    
    child_nodes: Mapped[List["MindMapNode"]] = relationship(
        "MindMapNode",
        back_populates="parent_node",
        cascade="all, delete-orphan"
    )
    
    # Indexes for efficient queries based on Issue #5 requirements
    __table_args__ = (
        Index("idx_mindmap_video_parent", "video_id", "parent_node_id"),
        Index("idx_mindmap_video_depth", "video_id", "depth"),
        Index("idx_mindmap_parent_order", "parent_node_id", "display_order"),
        Index("idx_mindmap_timestamps", "video_id", "timestamp_start", "timestamp_end"),
        Index("idx_mindmap_node_type", "node_type"),
        Index("idx_mindmap_importance", "importance"),
        Index("idx_mindmap_confidence", "confidence"),
    )
    
    def __repr__(self) -> str:
        return f"<MindMapNode(id='{self.id}', type='{self.node_type}', depth={self.depth}, summary='{self.summary[:30]}...')>"
    
    @property
    def is_root_node(self) -> bool:
        """Check if this is a root node (no parent)"""
        return self.parent_node_id is None or self.node_type == "root"
    
    @property
    def has_children(self) -> bool:
        """Check if this node has child nodes"""
        return len(self.child_nodes) > 0
    
    @property
    def duration(self) -> float:
        """Get the duration of this node segment in seconds"""
        return self.timestamp_end - self.timestamp_start
    
    @property
    def position(self) -> Dict[str, Optional[float]]:
        """Get position coordinates as dictionary"""
        return {
            "x": self.position_x,
            "y": self.position_y
        }
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get analysis metadata"""
        return {
            "confidence": self.confidence,
            "importance": self.importance,
            "word_count": self.word_count,
            **self.analysis_metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation matching Issue #5 interface"""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "parent_node_id": self.parent_node_id,
            "content": self.content,
            "summary": self.summary,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "node_type": self.node_type,
            "depth": self.depth,
            "children": [child.id for child in self.child_nodes],
            "keywords": self.keywords or [],
            "position": self.position,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_path_to_root(self) -> List[str]:
        """Get the path from this node to root as list of node IDs"""
        path = [self.id]
        current_node = self
        while current_node.parent_node_id:
            path.append(current_node.parent_node_id)
            current_node = current_node.parent_node
        return list(reversed(path))
    
    def get_all_descendants(self) -> List["MindMapNode"]:
        """Get all descendant nodes recursively"""
        descendants = []
        for child in self.child_nodes:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_siblings(self) -> List["MindMapNode"]:
        """Get all sibling nodes (same parent)"""
        if self.parent_node:
            return [child for child in self.parent_node.child_nodes if child.id != self.id]
        return []
    
    @classmethod
    def get_by_video_id(cls, session, video_id: str) -> List["MindMapNode"]:
        """Get all nodes for a video"""
        return session.query(cls).filter(cls.video_id == video_id).all()
    
    @classmethod
    def get_root_nodes(cls, session, video_id: str) -> List["MindMapNode"]:
        """Get root nodes for a video"""
        return session.query(cls).filter(
            cls.video_id == video_id,
            cls.node_type == "root"
        ).all()
    
    @classmethod
    def get_by_depth(cls, session, video_id: str, depth: int) -> List["MindMapNode"]:
        """Get nodes at specific depth for a video"""
        return session.query(cls).filter(
            cls.video_id == video_id,
            cls.depth == depth
        ).all()
    
    @classmethod
    def get_by_timestamp_range(cls, session, video_id: str, start_time: float, end_time: float) -> List["MindMapNode"]:
        """Get nodes within timestamp range"""
        return session.query(cls).filter(
            cls.video_id == video_id,
            cls.timestamp_start >= start_time,
            cls.timestamp_end <= end_time
        ).all()
    
    @classmethod
    def get_by_node_type(cls, session, video_id: str, node_type: str) -> List["MindMapNode"]:
        """Get nodes by type for a video"""
        return session.query(cls).filter(
            cls.video_id == video_id,
            cls.node_type == node_type
        ).all()