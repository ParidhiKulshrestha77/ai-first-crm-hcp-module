import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { api } from "./api/client";
import { fetchHCPs, selectHCP } from "./store/slices/hcpSlice";
import LogInteractionScreen from "./components/LogInteractionScreen.jsx";

export default function App() {
  const dispatch = useDispatch();
  const { list, selectedId, status } = useSelector((s) => s.hcps);
  const [demoBusy, setDemoBusy] = useState(false);

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  useEffect(() => {
    const bootstrap = async () => {
      if (list.length === 0 && status !== "loading") {
        try {
          await api.seedDemoData();
          dispatch(fetchHCPs());
        } catch (error) {
          console.warn("Demo seed failed", error);
        }
      }
    };

    bootstrap();
  }, [dispatch, list.length, status]);

  const handleDemoSeed = async () => {
    setDemoBusy(true);
    try {
      await api.seedDemoData();
      await dispatch(fetchHCPs());
    } finally {
      setDemoBusy(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">AI</span>
          <div>
            <h1>HCP Interaction Log</h1>
            <p>AI-first CRM · Healthcare Professional module</p>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="demo-badge">Demo mode</div>
          <button type="button" className="demo-btn" onClick={handleDemoSeed} disabled={demoBusy}>
            {demoBusy ? "Seeding…" : "Seed demo data"}
          </button>
          <div className="hcp-picker">
            <label htmlFor="hcp-select">Healthcare Professional</label>
            <select
              id="hcp-select"
              value={selectedId || ""}
              onChange={(e) => dispatch(selectHCP(e.target.value))}
              disabled={status === "loading" || list.length === 0}
            >
              {list.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} — {h.specialty || "General"} (Tier {h.tier})
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <main>
        {selectedId ? (
          <LogInteractionScreen hcpId={selectedId} />
        ) : (
          <p className="empty-state">
            No HCPs yet — run <code>POST /api/dev/seed</code> on the backend, then refresh.
          </p>
        )}
      </main>
    </div>
  );
}
