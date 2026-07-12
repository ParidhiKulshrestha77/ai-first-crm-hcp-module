"""
The LangGraph agent's tool belt.

Assignment requires >= 5 tools including Log Interaction and Edit Interaction.
This file ships 7:

  1. log_interaction        (required)
  2. edit_interaction       (required)
  3. schedule_followup
  4. analyze_sentiment
  5. track_sample_drop
  6. check_compliance        <- unique: flags potential off-label / regulatory risk
  7. summarize_hcp_history   <- unique: pre-call briefing generator

Each tool is a thin, auditable wrapper: it does ONE job, writes/reads the DB
itself (short-lived session), and returns a small JSON-serialisable dict so
it can be dropped straight into the ToolMessage the graph sends back to the
LLM, and into AgentTraceLog for the UI's live trace panel.
"""
import json
from datetime import datetime, timedelta
from typing import Optional

from langchain_core.tools import tool
from langchain_groq import ChatGroq

from app.database import SessionLocal
from app.models import HCP, Interaction, InteractionChannel, InteractionType
from app.config import get_settings

settings = get_settings()

_extraction_llm = ChatGroq(model=settings.primary_model, api_key=settings.groq_api_key, temperature=0)
# Heavier model reserved for tasks that need more reasoning depth (multi-visit
# synthesis, compliance nuance) rather than single-note extraction.
_reasoning_llm = ChatGroq(model=settings.context_model, api_key=settings.groq_api_key, temperature=0.1)


def _llm_json_reasoning(prompt: str) -> dict:
    resp = _reasoning_llm.invoke(prompt)
    text = resp.content.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}



def _llm_json(prompt: str) -> dict:
    """Call Groq and force-parse JSON out of the response, tolerating stray text."""
    resp = _extraction_llm.invoke(prompt)
    text = resp.content.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


# ---------------------------------------------------------------------------
# 1. LOG INTERACTION (required)
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_id: str,
    raw_notes: str,
    channel: str = "chat",
    interaction_type: str = "in_person_visit",
    products_discussed: Optional[list[str]] = None,
) -> dict:
    """
    Log a new HCP interaction. Uses the LLM to summarize the free-text notes
    and extract structured entities (products mentioned, topics, objections,
    sentiment cues, requested follow-ups) so the rep doesn't have to fill
    every field by hand. Call this whenever the rep describes a visit/call
    that hasn't been saved yet.
    """
    extraction_prompt = f"""Extract structured data from this pharma sales rep's field note
about a healthcare professional (HCP) interaction. Return ONLY valid JSON with keys:
"summary" (1-2 sentence summary), "products_discussed" (list of drug/product names mentioned),
"topics" (list of short topic tags), "objections" (list of any pushback/concerns raised),
"requested_materials" (list), "sentiment" (one of positive/neutral/negative).

Field note:
\"\"\"{raw_notes}\"\"\"

JSON:"""
    try:
        extracted = _llm_json(extraction_prompt)
    except Exception as e:
        print(f"ERROR: LLM extraction failed: {str(e)}")
        extracted = {
            "summary": raw_notes[:200],
            "products_discussed": products_discussed or [],
            "topics": [],
            "objections": [],
            "requested_materials": [],
            "sentiment": "neutral"
        }

    db = SessionLocal()
    try:
        hcp = db.get(HCP, hcp_id)
        if not hcp:
            return {"error": f"No HCP found with id {hcp_id}"}

        interaction = Interaction(
            hcp_id=hcp_id,
            channel=InteractionChannel(channel) if channel in InteractionChannel._value2member_map_ else InteractionChannel.CHAT,
            interaction_type=InteractionType(interaction_type) if interaction_type in InteractionType._value2member_map_ else InteractionType.IN_PERSON_VISIT,
            raw_notes=raw_notes,
            ai_summary=extracted.get("summary", raw_notes[:200]),
            entities={
                "topics": extracted.get("topics", []),
                "objections": extracted.get("objections", []),
                "requested_materials": extracted.get("requested_materials", []),
            },
            products_discussed=products_discussed or extracted.get("products_discussed", []),
            sentiment=extracted.get("sentiment", "neutral"),
            edit_history=[],
        )
        db.add(interaction)

        # nudge the HCP's rolling engagement score
        bump = {"positive": 5, "neutral": 1, "negative": -3}.get(interaction.sentiment, 0)
        hcp.engagement_score = round((hcp.engagement_score or 0) + bump, 2)

        db.commit()
        db.refresh(interaction)
        return {
            "status": "logged",
            "interaction_id": interaction.id,
            "summary": interaction.ai_summary,
            "sentiment": interaction.sentiment,
            "products_discussed": interaction.products_discussed,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. EDIT INTERACTION (required)
# ---------------------------------------------------------------------------
@tool
def edit_interaction(
    interaction_id: str,
    updated_notes: Optional[str] = None,
    products_discussed: Optional[list[str]] = None,
    edited_by: str = "field_rep",
    reason: Optional[str] = None,
) -> dict:
    """
    Modify a previously logged interaction (e.g. correcting a product name,
    adding detail the rep forgot). Every edit is appended to an audit trail
    (edit_history) with a timestamp and reason, since pharma CRM edits must
    stay traceable for compliance review. If updated_notes is supplied, the
    AI summary is regenerated.
    """
    db = SessionLocal()
    try:
        interaction = db.get(Interaction, interaction_id)
        if not interaction:
            return {"error": f"No interaction found with id {interaction_id}"}

        changes = {}
        if updated_notes is not None and updated_notes != interaction.raw_notes:
            changes["raw_notes"] = {"old": interaction.raw_notes, "new": updated_notes}
            interaction.raw_notes = updated_notes
            resummarized = _llm_json(
                f'Summarize this HCP interaction note in one sentence. Return JSON {{"summary": "..."}}.\n\n"{updated_notes}"'
            )
            interaction.ai_summary = resummarized.get("summary", interaction.ai_summary)

        if products_discussed is not None:
            changes["products_discussed"] = {"old": interaction.products_discussed, "new": products_discussed}
            interaction.products_discussed = products_discussed

        history = interaction.edit_history or []
        history.append({
            "edited_by": edited_by,
            "reason": reason,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat(),
        })
        interaction.edit_history = history
        interaction.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(interaction)
        return {
            "status": "updated",
            "interaction_id": interaction.id,
            "ai_summary": interaction.ai_summary,
            "edit_count": len(history),
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. SCHEDULE FOLLOW-UP
# ---------------------------------------------------------------------------
@tool
def schedule_followup(interaction_id: str, days_from_now: int = 14, note: Optional[str] = None) -> dict:
    """
    Set or update the next-best-action follow-up date for an interaction.
    Defaults to a 14-day cadence, which is typical for HCP call planning.
    """
    db = SessionLocal()
    try:
        interaction = db.get(Interaction, interaction_id)
        if not interaction:
            return {"error": f"No interaction found with id {interaction_id}"}
        interaction.followup_date = datetime.utcnow() + timedelta(days=days_from_now)
        if note:
            interaction.next_best_action = note
        db.commit()
        return {
            "status": "scheduled",
            "followup_date": interaction.followup_date.isoformat(),
            "next_best_action": interaction.next_best_action,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. ANALYZE SENTIMENT
# ---------------------------------------------------------------------------
@tool
def analyze_sentiment(text: str) -> dict:
    """
    Run standalone sentiment/receptiveness analysis on a snippet of text
    (e.g. rep's raw impression of how the HCP reacted). Returns a label and
    a -1..1 score. Useful mid-conversation, before the interaction is saved.
    """
    result = _llm_json(
        f'Classify the sentiment of this pharma-rep note about an HCP\'s reaction. '
        f'Return ONLY JSON: {{"sentiment": "positive|neutral|negative", "score": <float -1 to 1>, "reason": "..."}}.\n\n'
        f'Note: "{text}"'
    )
    return {
        "sentiment": result.get("sentiment", "neutral"),
        "score": result.get("score", 0.0),
        "reason": result.get("reason", ""),
    }


# ---------------------------------------------------------------------------
# 5. TRACK SAMPLE DROP
# ---------------------------------------------------------------------------
@tool
def track_sample_drop(interaction_id: str, samples: dict[str, int]) -> dict:
    """
    Record drug samples left with the HCP during this interaction, e.g.
    {"DrugA 10mg": 20, "DrugB": 10}. Pharma sample distribution is tightly
    regulated (PDMA), so every drop must be tied to a specific interaction.
    """
    db = SessionLocal()
    try:
        interaction = db.get(Interaction, interaction_id)
        if not interaction:
            return {"error": f"No interaction found with id {interaction_id}"}
        existing = interaction.samples_dropped or {}
        for k, v in samples.items():
            existing[k] = existing.get(k, 0) + v
        interaction.samples_dropped = existing
        db.commit()
        return {"status": "recorded", "samples_dropped": existing}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 6. CHECK COMPLIANCE  (unique / advanced)
# ---------------------------------------------------------------------------
@tool
def check_compliance(interaction_id: str) -> dict:
    """
    Screen an interaction's notes for potential regulatory risk: off-label
    promotion claims, unsubstantiated efficacy/safety claims, or improper
    incentive language. Flags the interaction for compliance review rather
    than blocking the rep -- this keeps the agent useful in a regulated
    life-sciences workflow instead of just a generic note-taker.
    """
    db = SessionLocal()
    try:
        interaction = db.get(Interaction, interaction_id)
        if not interaction or not interaction.raw_notes:
            return {"error": "Interaction not found or has no notes"}

        result = _llm_json(f"""You are a pharma compliance screener. Review this field rep's note for
potential off-label promotion, unsubstantiated claims, or improper incentives.
Return ONLY JSON: {{"flagged": true/false, "risk_level": "none|low|medium|high", "notes": "short explanation"}}.

Note: \"\"\"{interaction.raw_notes}\"\"\"
""")
        interaction.compliance_flagged = bool(result.get("flagged", False))
        interaction.compliance_notes = result.get("notes", "")
        db.commit()
        return {
            "interaction_id": interaction_id,
            "flagged": interaction.compliance_flagged,
            "risk_level": result.get("risk_level", "none"),
            "notes": interaction.compliance_notes,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 7. SUMMARIZE HCP HISTORY  (unique / advanced)
# ---------------------------------------------------------------------------
@tool
def summarize_hcp_history(hcp_id: str, limit: int = 5) -> dict:
    """
    Generate a pre-call briefing for a rep about to visit an HCP: pulls the
    last N logged interactions and has the LLM synthesize a short prep
    summary (recurring objections, preferred products, relationship trend).
    """
    db = SessionLocal()
    try:
        hcp = db.get(HCP, hcp_id)
        if not hcp:
            return {"error": f"No HCP found with id {hcp_id}"}
        history = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.created_at.desc())
            .limit(limit)
            .all()
        )
        if not history:
            return {"hcp": hcp.name, "briefing": "No prior interactions on record. This will be a first touchpoint."}

        bullets = "\n".join(f"- ({i.created_at.date()}) {i.ai_summary}" for i in reversed(history))
        result = _llm_json_reasoning(f"""Given this chronological history of a sales rep's interactions with
Dr. {hcp.name} ({hcp.specialty or "specialty unknown"}), write a short pre-call briefing.
Return ONLY JSON: {{"briefing": "2-3 sentences", "recommended_focus": "1 sentence"}}.

History:
{bullets}
""")
        return {
            "hcp": hcp.name,
            "engagement_score": hcp.engagement_score,
            "briefing": result.get("briefing", ""),
            "recommended_focus": result.get("recommended_focus", ""),
            "interactions_reviewed": len(history),
        }
    finally:
        db.close()


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    schedule_followup,
    analyze_sentiment,
    track_sample_drop,
    check_compliance,
    summarize_hcp_history,
]
