import enum
import uuid
from datetime import datetime

from sqlalchemy import (Column, String, DateTime, Text, Enum, ForeignKey,
                         Table, Float)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class InteractionTypeEnum(str, enum.Enum):
    meeting = "Meeting"
    call = "Call"
    email = "Email"
    conference = "Conference"
    virtual = "Virtual Meeting"


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    material_type = Column(String, default="brochure")  # brochure, deck, sample-card


# association-like simple tables stored as arrays of names for simplicity in this scaffold
class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    hcp_id = Column(UUID(as_uuid=False), ForeignKey("hcps.id"), nullable=False)
    rep_id = Column(String, nullable=True)  # field rep user id, from auth
    interaction_type = Column(Enum(InteractionTypeEnum), default=InteractionTypeEnum.meeting)
    date = Column(DateTime, default=datetime.utcnow)
    attendees = Column(ARRAY(String), default=list)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(ARRAY(String), default=list)
    samples_distributed = Column(ARRAY(String), default=list)
    sentiment = Column(Enum(SentimentEnum), default=SentimentEnum.neutral)
    sentiment_confidence = Column(Float, nullable=True)
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    source = Column(String, default="form")  # "form" or "chat"
    raw_voice_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class ChatMessage(Base):
    """Stores conversational-logging turns per session, so the LangGraph agent
    can resume multi-turn slot-filling for the chat-based logging flow."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String)  # user | assistant | tool
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
