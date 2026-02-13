"""SQLAlchemy database models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, DateTime, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Document(Base):
    """Document model - stores source documents"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), default="text"
    )  # 'text' or 'url'
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    nodes: Mapped[List["Node"]] = relationship(
        "Node", back_populates="source_document", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, source_type={self.source_type})>"


class Node(Base):
    """Node model - represents entities in the knowledge graph"""

    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="nodes", lazy="selectin"
    )
    outgoing_edges: Mapped[List["Edge"]] = relationship(
        "Edge",
        foreign_keys="[Edge.source_id]",
        back_populates="source_node",
        lazy="selectin",
    )
    incoming_edges: Mapped[List["Edge"]] = relationship(
        "Edge",
        foreign_keys="[Edge.target_id]",
        back_populates="target_node",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("idx_nodes_name", "name"),
        Index("idx_nodes_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<Node(id={self.id}, name={self.name}, type={self.type})>"


class Edge(Base):
    """Edge model - represents relations between nodes"""

    __tablename__ = "edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_node: Mapped["Node"] = relationship(
        "Node",
        foreign_keys=[source_id],
        back_populates="outgoing_edges",
        lazy="selectin",
    )
    target_node: Mapped["Node"] = relationship(
        "Node",
        foreign_keys=[target_id],
        back_populates="incoming_edges",
        lazy="selectin",
    )

    # Indexes for efficient graph traversal
    __table_args__ = (
        Index("idx_edges_source", "source_id"),
        Index("idx_edges_target", "target_id"),
        Index("idx_edges_relation_type", "relation_type"),
    )

    def __repr__(self) -> str:
        return f"<Edge(id={self.id}, source_id={self.source_id}, target_id={self.target_id}, relation={self.relation_type})>"
