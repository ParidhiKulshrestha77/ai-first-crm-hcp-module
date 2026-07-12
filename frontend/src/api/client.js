const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listHCPs: () => request("/hcps"),
  createHCP: (payload) => request("/hcps", { method: "POST", body: JSON.stringify(payload) }),
  seedDemoData: () => request("/dev/seed", { method: "POST" }),

  listInteractions: (hcpId) => request(`/interactions${hcpId ? `?hcp_id=${hcpId}` : ""}`),
  createInteraction: (payload) => request("/interactions", { method: "POST", body: JSON.stringify(payload) }),
  updateInteraction: (id, payload) => request(`/interactions/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  chat: (payload) => request("/chat", { method: "POST", body: JSON.stringify(payload) }),

  // Returns the raw Response so callers can read the SSE stream themselves.
  chatStream: (payload) =>
    fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
