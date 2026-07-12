import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class InteractionChannel(str, enum.Enum):
    FORM = "form"
    CHAT = "chat"
    VOICE = "voice"


class InteractionType(str, enum.Enum):
    IN_PERSON_VISIT = "in_person_visit"
    VIRTUAL_CALL = "virtual_call"
    PHONE_CALL = "phone_call"
    CONFERENCE = "conference_booth"
    SAMPLE_DROP = "sample_drop"
    EMAIL = "email"


class HCP(Base):
    """A Healthcare Professional the field rep engages with."""
    __tablename__ = "hcps"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    tier = Column(String, default="B")  # A/B/C call-priority tier
    engagement_score = Column(Float, default=0.0)  # rolling AI-derived score
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged interaction with an HCP."""
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    hcp_id = Column(String, ForeignKey("hcps.id"), nullable=False)

    channel = Column(Enum(InteractionChannel), default=InteractionChannel.FORM)
    interaction_type = Column(Enum(InteractionType), default=InteractionType.IN_PERSON_VISIT)

    raw_notes = Column(Text, nullable=True)          # verbatim rep input (form notes or chat transcript)
    ai_summary = Column(Text, nullable=True)          # LLM-generated summary
    entities = Column(JSON, nullable=True)            # extracted entities: drugs, topics, objections
    products_discussed = Column(JSON, nullable=True)  # list[str]
    samples_dropped = Column(JSON, nullable=True)     # {"product": qty}
    sentiment = Column(String, nullable=True)          # positive/neutral/negative
    sentiment_score = Column(Float, nullable=True)      # -1..1
    next_best_action = Column(Text, nullable=True)      # AI-suggested follow-up
    followup_date = Column(DateTime, nullable=True)

    compliance_flagged = Column(Boolean, default=False)
    compliance_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edit_history = Column(JSON, default=list)  # audit trail of edits (who/when/what changed)

    hcp = relationship("HCP", back_populates="interactions")


class AgentTraceLog(Base):
    """
    Persisted trace of every LangGraph node the agent visited while handling
    a request. Powers the live 'Agent Reasoning Trace' panel in the UI and
    doubles as an audit log (important in a regulated pharma context).
    """
    __tablename__ = "agent_trace_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, index=True)
    node_name = Column(String)
    tool_name = Column(String, nullable=True)
    input_snapshot = Column(JSON, nullable=True)
    output_snapshot = Column(JSON, nullable=True)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
