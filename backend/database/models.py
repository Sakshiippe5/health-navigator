# database/models.py
#
# RESPONSIBILITY: Define all database tables as Python classes.
# SQLAlchemy maps these classes to PostgreSQL tables.
#
# Tables:
#   User         → registered users
#   Document     → uploaded PDFs per user
#   ChatSession  → conversation sessions
#   Message      → individual chat messages
#   AgentResult  → saved agent assessments

from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, Text, Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class User(Base):
    """
    Stores registered users.
    password_hash = bcrypt hashed password (never plain text!)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships — one user has many documents/sessions
    documents = relationship("Document", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="user")
    agent_results = relationship("AgentResult", back_populates="user")


class Document(Base):
    """
    Tracks uploaded PDFs per user.
    Links file on disk (file_id) to the user who uploaded it.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    size_mb = Column(Float, nullable=False)
    is_embedded = Column(Boolean, default=False)
    total_chunks = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to user
    owner = relationship("User", back_populates="documents")
    chat_sessions = relationship("ChatSession", back_populates="document")


class ChatSession(Base):
    """
    Represents one conversation about one document.
    Replaces our in-memory chat_sessions dict.
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session")


class Message(Base):
    """
    Individual messages in a chat session.
    role = "user" or "assistant"
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"))
    role = Column(String, nullable=False)      # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("ChatSession", back_populates="messages")


class AgentResult(Base):
    """
    Saves results from AI agent runs.
    Lets users review past assessments.
    """
    __tablename__ = "agent_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_type = Column(String, nullable=False)  # "symptom", "drug", "pipeline"
    input_data = Column(JSON, nullable=False)     # what was sent
    result_data = Column(JSON, nullable=False)    # what came back
    urgency_level = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="agent_results")