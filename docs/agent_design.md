# Agent & Tool Design — Extended Write-up

## The role of the LangGraph agent

The agent is the single point of intelligence behind the Log Interaction
screen. It does not replace the CRM's data model — it *populates and
maintains* it. Concretely, it:

- Turns unstructured rep input (typed, dictated, or chatted) into the
  structured `Interaction` record the rest of the CRM depends on.
- Decides, per turn, which of its 7 tools are relevant — a rep saying
  "actually change that to CardioFlow 20mg" should trigger `edit_interaction`,
  not a fresh `log_interaction`, and the agent makes that call itself rather
  than the frontend hard-coding intent detection.
- Runs supporting analysis (sentiment, compliance) proactively, without the
  rep having to ask, because those are things a compliant CRM should always
  capture, not optional extras.
- Reports back in plain language ("Logged the visit with Dr. Mehra — flagged
  for compliance review because of the off-label comment") so the rep always
  knows what happened to their data.

It intentionally does **not** try to be a general-purpose assistant. The
system prompt (`backend/app/agent/graph.py`) scopes it tightly to HCP
interaction management and tells it never to fabricate an `hcp_id` — if the
context is ambiguous, it should ask rather than guess, which matters a lot
in a regulated data-entry context.

## Graph structure

```
        ┌─────────┐   tool call?   ┌─────────┐
 START →│  agent  │───────Yes─────→│  tools  │
        │ (Groq)  │←────────────────┘
        └────┬────┘
             │ No tool call
             ▼
            END
```

This is LangGraph's standard ReAct loop (`tools_condition` +
`ToolNode(ALL_TOOLS)`), chosen deliberately over a more elaborate
multi-agent graph: with 7 well-scoped tools and a single responsibility
(interaction logging), a second "supervisor" layer would add latency and
complexity without adding capability. The loop can call multiple tools in
sequence within one user turn (e.g. `log_interaction` → `check_compliance` →
`schedule_followup`), which is exactly what the sample conversation below
does.

## The 7 tools

### 1. `log_interaction` (required)
**Input:** `hcp_id`, `raw_notes`, `channel`, `interaction_type`, optional `products_discussed`.
**What it does:** Sends the raw notes to Gemma2-9B with an extraction prompt
that returns a one-line summary, product/topic/objection lists, requested
materials, and a sentiment label — all as JSON. Persists an `Interaction`
row with both the raw notes (verbatim, for audit) and the AI-derived fields,
then adjusts the HCP's rolling `engagement_score`.
**Why an LLM and not regex/keyword matching:** rep notes are free text
("she pushed back on cost but wants the elderly-patient data") — the
objection, the sentiment, and the follow-up ask are all in one sentence with
no fixed structure to pattern-match against.

### 2. `edit_interaction` (required)
**Input:** `interaction_id`, optional `updated_notes` / `products_discussed`, `edited_by`, `reason`.
**What it does:** Applies the change, re-summarizes if notes changed, and
appends `{edited_by, reason, changes, timestamp}` to `edit_history` — a full
audit trail rather than a silent overwrite, which matters because pharma
CRM records are subject to compliance review.

### 3. `schedule_followup`
Sets a `followup_date` (default +14 days, the typical HCP call cadence) and
an optional `next_best_action` note on an interaction.

### 4. `analyze_sentiment`
Standalone sentiment scoring for a piece of text, independent of any saved
record — useful when the rep is still describing the visit and hasn't
committed anything yet ("how did that sound to you so far?").

### 5. `track_sample_drop`
Records `{product: quantity}` samples against a specific interaction.
Sample distribution is one of the most heavily regulated activities a rep
does (PDMA in the US), so it's modeled as its own auditable action rather
than a free-text field.

### 6. `check_compliance` — unique
Re-reads an interaction's notes and asks the LLM to flag potential
off-label promotion, unsubstantiated claims, or improper incentive
language, returning a risk level and a short explanation. This is run
automatically after every form submission and is available to the chat
agent to invoke proactively. It flags for **human review** rather than
blocking the rep — the goal is visibility for a compliance team, not an
opinionated gatekeeper.

### 7. `summarize_hcp_history` — unique
Pulls the last N interactions for an HCP and asks the *larger*
`llama-3.3-70b-versatile` model (routed separately from the fast
`gemma2-9b-it` used for single-note extraction) to produce a short pre-call
briefing: recurring objections, relationship trend, and a recommended focus
for the next visit. This is the tool a rep would call from the car in the
parking lot before walking in to see the same doctor again.

## Sample conversation (what the video demo shows)

```
Rep:   Just left Dr. Mehra's office. Discussed CardioFlow 10mg for her
       elderly hypertensive patients. She was receptive but wants efficacy
       data specific to over-65s before prescribing. Left 15 samples.
       Follow up in 2 weeks.

Agent: → log_interaction(hcp_id=..., raw_notes="...")
       → check_compliance(interaction_id=...)
       → track_sample_drop(interaction_id=..., samples={"CardioFlow 10mg": 15})
       → schedule_followup(interaction_id=..., days_from_now=14)

Agent: "Logged your visit with Dr. Mehra — positive sentiment, she's asking
       for elderly-specific efficacy data before prescribing CardioFlow
       10mg. Recorded 15 samples dropped. Compliance clear. Follow-up set
       for two weeks out."

Rep:   Actually make that 20 samples, I miscounted.

Agent: → edit_interaction(interaction_id=..., ...)
       "Updated — 20 samples logged, with your correction noted in the
       audit trail."
```

Every arrow above is a real tool call visible live in the Agent Reasoning
Trace panel in the UI while the conversation happens.
