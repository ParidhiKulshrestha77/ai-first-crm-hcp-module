import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/client";

export const fetchHCPs = createAsyncThunk("hcps/fetch", () => api.listHCPs());

const hcpSlice = createSlice({
  name: "hcps",
  initialState: { list: [], selectedId: null, status: "idle" },
  reducers: {
    selectHCP(state, action) {
      state.selectedId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.list = action.payload;
        if (!state.selectedId && action.payload.length) {
          state.selectedId = action.payload[0].id;
        }
      })
      .addCase(fetchHCPs.rejected, (state) => {
        state.status = "failed";
      });
  },
});

export const { selectHCP } = hcpSlice.actions;
export default hcpSlice.reducer;
