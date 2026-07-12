from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.agent.tools import log_interaction, edit_interaction, check_compliance

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.created_at.desc()).all()


@router.post("", response_model=schemas.InteractionOut, status_code=201)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """
    Structured-form submission path. Reuses the SAME log_interaction tool
    the chat agent uses, so form and chat produce identical, consistently
    AI-enriched records -- one source of truth, two ways to fill it in.
    """
    try:
        result = log_interaction.invoke({
            "hcp_id": payload.hcp_id,
            "raw_notes": payload.raw_notes,
            "channel": payload.channel,
            "interaction_type": payload.interaction_type,
            "products_discussed": payload.products_discussed,
        })
    except Exception as e:
        raise HTTPException(500, f"Tool error: {str(e)}")
    if "error" in result:
        raise HTTPException(400, result["error"])

    interaction = db.get(models.Interaction, result["interaction_id"])

    if payload.samples_dropped:
        from app.agent.tools import track_sample_drop
        track_sample_drop.invoke({
            "interaction_id": interaction.id,
            "samples": payload.samples_dropped,
        })
    if payload.followup_date:
        interaction.followup_date = payload.followup_date
        db.commit()

    # Run a compliance pass automatically -- consistent with what the agent does in chat.
    check_compliance.invoke({"interaction_id": interaction.id})

    db.refresh(interaction)
    return interaction


@router.patch("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    result = edit_interaction.invoke({
        "interaction_id": interaction_id,
        "updated_notes": payload.raw_notes,
        "products_discussed": payload.products_discussed,
        "edited_by": payload.edited_by,
        "reason": payload.reason,
    })
    if "error" in result:
        raise HTTPException(404, result["error"])
    return db.get(models.Interaction, interaction_id)


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.get(models.Interaction, interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction
