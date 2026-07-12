import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/client";

export const fetchInteractions = createAsyncThunk(
  "interactions/fetch",
  (hcpId) => api.listInteractions(hcpId)
);

export const submitInteraction = createAsyncThunk(
  "interactions/submit",
  async (payload) => api.createInteraction(payload)
);

export const editInteraction = createAsyncThunk(
  "interactions/edit",
  async ({ id, ...payload }) => api.updateInteraction(id, payload)
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: { list: [], status: "idle", submitStatus: "idle", error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.list = action.payload;
      })
      .addCase(submitInteraction.pending, (state) => {
        state.submitStatus = "loading";
        state.error = null;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.submitStatus = "succeeded";
        state.list.unshift(action.payload);
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.submitStatus = "failed";
        state.error = action.error.message;
      })
      .addCase(editInteraction.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.list[idx] = action.payload;
      });
  },
});

export default interactionsSlice.reducer;
