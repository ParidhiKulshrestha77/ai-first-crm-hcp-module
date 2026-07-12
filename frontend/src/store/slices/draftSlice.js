import { createSlice } from "@reduxjs/toolkit";

// Keeps an in-memory draft of the form so switching between the Form and
// Chat tabs (or a dropped connection mid-visit) never loses the rep's notes.
// A real deployment would persist this to IndexedDB and flush a sync queue
// once connectivity returns -- the shape here is built to drop straight into
// that without changing the reducer contract.
const draftSlice = createSlice({
  name: "draft",
  initialState: {
    hcpId: null,
    rawNotes: "",
    productsDiscussed: [],
    interactionType: "in_person_visit",
    lastSavedAt: null,
    syncStatus: "synced", // synced | pending | offline
  },
  reducers: {
    updateDraft(state, action) {
      Object.assign(state, action.payload, { lastSavedAt: Date.now(), syncStatus: "pending" });
    },
    markSynced(state) {
      state.syncStatus = "synced";
    },
    markOffline(state) {
      state.syncStatus = "offline";
    },
    clearDraft(state) {
      state.rawNotes = "";
      state.productsDiscussed = [];
      state.lastSavedAt = null;
      state.syncStatus = "synced";
    },
  },
});

export const { updateDraft, markSynced, markOffline, clearDraft } = draftSlice.actions;
export default draftSlice.reducer;
