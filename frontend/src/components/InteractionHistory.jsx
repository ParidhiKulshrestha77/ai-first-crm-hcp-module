import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { editInteraction } from "../store/slices/interactionsSlice";
import ComplianceBadge from "./ComplianceBadge.jsx";

const SENTIMENT_COLOR = { positive: "#1a7f37", neutral: "#8a6d00", negative: "#b3261e" };

export default function InteractionHistory({ hcpId }) {
  const dispatch = useDispatch();
  const { list, status } = useSelector((s) => s.interactions);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const startEdit = (interaction) => {
    setEditingId(interaction.id);
    setEditText(interaction.raw_notes || "");
  };

  const saveEdit = async (id) => {
    await dispatch(editInteraction({ id, raw_notes: editText, reason: "Manual correction from history panel" }));
    setEditingId(null);
  };

  return (
    <div className="history-panel">
      <h3>🗂️ Interaction History</h3>
      {status === "loading" && <p>Loading…</p>}
      {list.length === 0 && status !== "loading" && <p className="trace-empty">No interactions logged yet for this HCP.</p>}
      <ul className="history-list">
        {list.map((i) => (
          <li key={i.id} className="history-item">
            <div className="history-item-header">
              <span className="history-type">{i.interaction_type.replaceAll("_", " ")}</span>
              <span className="history-date">{new Date(i.created_at).toLocaleDateString()}</span>
            </div>

            {editingId === i.id ? (
              <div className="edit-box">
                <textarea rows={4} value={editText} onChange={(e) => setEditText(e.target.value)} />
                <div className="edit-actions">
                  <button onClick={() => saveEdit(i.id)}>Save</button>
                  <button className="link-btn" onClick={() => setEditingId(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <p className="history-summary">{i.ai_summary}</p>
                {i.products_discussed?.length > 0 && (
                  <p className="history-products">💊 {i.products_discussed.join(", ")}</p>
                )}
                <div className="history-meta">
                  <span style={{ color: SENTIMENT_COLOR[i.sentiment] || "#666" }}>● {i.sentiment}</span>
                  <ComplianceBadge flagged={i.compliance_flagged} notes={i.compliance_notes} />
                  {i.edit_history?.length > 0 && <span className="edit-count">{i.edit_history.length} edit(s)</span>}
                </div>
                <button className="link-btn" onClick={() => startEdit(i)}>Edit</button>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
