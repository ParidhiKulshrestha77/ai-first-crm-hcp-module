from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tier: Optional[str] = "B"


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    engagement_score: float
    created_at: datetime


class InteractionCreate(BaseModel):
    hcp_id: str
    channel: str = "form"
    interaction_type: str = "in_person_visit"
    raw_notes: str
    products_discussed: Optional[list[str]] = None
    samples_dropped: Optional[dict[str, int]] = None
    followup_date: Optional[datetime] = None


class InteractionUpdate(BaseModel):
    raw_notes: Optional[str] = None
    products_discussed: Optional[list[str]] = None
    samples_dropped: Optional[dict[str, int]] = None
    followup_date: Optional[datetime] = None
    edited_by: str = "field_rep"
    reason: Optional[str] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    hcp_id: str
    channel: str
    interaction_type: str
    raw_notes: Optional[str]
    ai_summary: Optional[str]
    entities: Optional[Any]
    products_discussed: Optional[Any]
    samples_dropped: Optional[Any]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    next_best_action: Optional[str]
    followup_date: Optional[datetime]
    compliance_flagged: bool
    compliance_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    edit_history: Optional[Any]


class ChatMessage(BaseModel):
    session_id: str
    hcp_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    trace: list[dict]
    interaction: Optional[InteractionOut] = None
