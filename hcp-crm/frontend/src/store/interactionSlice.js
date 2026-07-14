import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { createInteraction, updateInteraction } from '../api/client'

const initialState = {
  hcpId: null,
  hcpName: '',
  interactionType: 'Meeting',
  date: new Date().toISOString().slice(0, 10),
  time: new Date().toTimeString().slice(0, 5),
  attendees: [],
  topicsDiscussed: '',
  materialsShared: [],
  samplesDistributed: [],
  sentiment: 'neutral',
  outcomes: '',
  followUpActions: '',
  suggestedFollowUps: [],
  savedInteractionId: null,
  status: 'idle', // idle | saving | saved | error
  error: null,
}

export const saveInteraction = createAsyncThunk(
  'interaction/save',
  async (_, { getState, rejectWithValue }) => {
    const s = getState().interaction
    if (!s.hcpId) return rejectWithValue('Select an HCP before saving.')
    const payload = {
      hcp_id: s.hcpId,
      interaction_type: s.interactionType,
      date: new Date(`${s.date}T${s.time}:00`).toISOString(),
      attendees: s.attendees,
      topics_discussed: s.topicsDiscussed,
      materials_shared: s.materialsShared,
      samples_distributed: s.samplesDistributed,
      sentiment: s.sentiment,
      outcomes: s.outcomes,
      follow_up_actions: s.followUpActions,
      source: 'form',
    }
    if (s.savedInteractionId) {
      const { data } = await updateInteraction(s.savedInteractionId, payload)
      return data
    }
    const { data } = await createInteraction(payload)
    return data
  }
)

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setHcp(state, action) {
      state.hcpId = action.payload.id
      state.hcpName = action.payload.name
    },
    setField(state, action) {
      const { field, value } = action.payload
      state[field] = value
    },
    addAttendee(state, action) {
      if (action.payload && !state.attendees.includes(action.payload)) {
        state.attendees.push(action.payload)
      }
    },
    removeAttendee(state, action) {
      state.attendees = state.attendees.filter((a) => a !== action.payload)
    },
    addMaterial(state, action) {
      state.materialsShared.push(action.payload)
    },
    addSample(state, action) {
      state.samplesDistributed.push(action.payload)
    },
    setSentiment(state, action) {
      state.sentiment = action.payload
    },
    /** Merge a draft produced by the AI chat agent's log_interaction / edit_interaction tool
     * straight into the structured form, so both logging paths stay in sync. */
    applyAgentDraft(state, action) {
      const d = action.payload
      if (d.id) state.savedInteractionId = d.id
      if (d.hcp_name) state.hcpName = d.hcp_name
      if (d.interaction_type) state.interactionType = d.interaction_type
      if (d.attendees) state.attendees = d.attendees
      if (d.topics_discussed) state.topicsDiscussed = d.topics_discussed
      if (d.materials_shared) state.materialsShared = d.materials_shared
      if (d.samples_distributed) state.samplesDistributed = d.samples_distributed
      if (d.sentiment) state.sentiment = d.sentiment
      if (d.outcomes) state.outcomes = d.outcomes
      if (d.follow_up_actions) state.followUpActions = d.follow_up_actions
    },
    setSuggestedFollowUps(state, action) {
      state.suggestedFollowUps = action.payload
    },
    resetForm() {
      return initialState
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveInteraction.pending, (state) => {
        state.status = 'saving'
        state.error = null
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.status = 'saved'
        state.savedInteractionId = action.payload.id
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.status = 'error'
        state.error = action.payload || action.error.message
      })
  },
})

export const {
  setHcp, setField, addAttendee, removeAttendee, addMaterial, addSample,
  setSentiment, applyAgentDraft, setSuggestedFollowUps, resetForm,
} = interactionSlice.actions

export default interactionSlice.reducer
