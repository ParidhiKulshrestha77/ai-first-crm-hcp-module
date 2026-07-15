import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { submitInteraction } from "../store/slices/interactionsSlice";
import { updateDraft, clearDraft, markSynced } from "../store/slices/draftSlice";
import VoiceInput from "./VoiceInput.jsx";

const INTERACTION_TYPES = [
  { value: "in_person_visit", label: "In-Person Visit" },
  { value: "virtual_call", label: "Virtual Call" },
  { value: "phone_call", label: "Phone Call" },
  { value: "conference_booth", label: "Conference Booth" },
  { value: "sample_drop", label: "Sample Drop" },
  { value: "email", label: "Email" },
];

export default function StructuredForm({ hcpId }) {
  const dispatch = useDispatch();
  const draft = useSelector((s) => s.draft);
  const { submitStatus, error } = useSelector((s) => s.interactions);
  const [productsText, setProductsText] = useState("");

  const handleNotesChange = (value) => {
    dispatch(updateDraft({ hcpId, rawNotes: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const products_discussed = productsText
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);

    const action = await dispatch(
      submitInteraction({
        hcp_id: hcpId,
        channel: "form",
        interaction_type: draft.interactionType,
        raw_notes: draft.rawNotes,
        products_discussed,
      })
    );
    if (submitInteraction.fulfilled.match(action)) {
      dispatch(clearDraft());
      dispatch(markSynced());
      setProductsText("");
    }
  };

  return (
    <form className="interaction-form" onSubmit={handleSubmit}>
      <div className="field">
        <label>Interaction Type</label>
        <select
          value={draft.interactionType}
          onChange={(e) => dispatch(updateDraft({ interactionType: e.target.value }))}
        >
          {INTERACTION_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>Products Discussed <span className="hint">(comma separated)</span></label>
        <input
          type="text"
          placeholder="e.g. CardioFlow 10mg, GlucoBalance"
          value={productsText}
          onChange={(e) => setProductsText(e.target.value)}
        />
      </div>

      <div className="field">
        <div className="field-header">
          <label>Visit Notes</label>
          <VoiceInput onTranscript={(text) => handleNotesChange(`${draft.rawNotes} ${text}`.trim())} />
        </div>
        <textarea
          rows={8}
          placeholder="Describe the interaction — what was discussed, HCP reaction, objections, requests…"
          value={draft.rawNotes}
          onChange={(e) => handleNotesChange(e.target.value)}
        />
        <p className="ai-hint">
          ✨ On submit, AI will auto-summarize, extract entities, score sentiment, and screen for
          compliance risk — no need to fill those fields manually.
        </p>
      </div>

      {error && <p className="form-error">{error}</p>}

      <button type="submit" disabled={submitStatus === "loading" || !draft.rawNotes.trim()}>
        {submitStatus === "loading" ? "Logging with AI…" : "Log Interaction"}
      </button>
    </form>
  );
}
