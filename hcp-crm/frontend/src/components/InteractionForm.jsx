import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  setHcp, setField, addAttendee, removeAttendee, saveInteraction,
} from '../store/interactionSlice'
import { searchHcps } from '../api/client'
import SentimentSelector from './SentimentSelector.jsx'
import MaterialsSamples from './MaterialsSamples.jsx'

const INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Conference', 'Virtual Meeting']

export default function InteractionForm() {
  const dispatch = useDispatch()
  const state = useSelector((s) => s.interaction)
  const [hcpQuery, setHcpQuery] = useState('')
  const [hcpResults, setHcpResults] = useState([])
  const [attendeeInput, setAttendeeInput] = useState('')

  async function onHcpSearch(value) {
    setHcpQuery(value)
    if (value.length < 2) { setHcpResults([]); return }
    const { data } = await searchHcps(value)
    setHcpResults(data)
  }

  return (
    <div className="panel form-panel">
      <h2 className="panel-title">Interaction Details</h2>

      <div className="grid-2">
        <div className="field">
          <label>HCP Name</label>
          <input
            placeholder="Search or select HCP..."
            value={hcpQuery || state.hcpName}
            onChange={(e) => onHcpSearch(e.target.value)}
          />
          {hcpResults.length > 0 && (
            <ul className="autocomplete">
              {hcpResults.map((h) => (
                <li key={h.id} onClick={() => { dispatch(setHcp(h)); setHcpQuery(''); setHcpResults([]) }}>
                  {h.name} {h.specialty ? `— ${h.specialty}` : ''}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="field">
          <label>Interaction Type</label>
          <select
            value={state.interactionType}
            onChange={(e) => dispatch(setField({ field: 'interactionType', value: e.target.value }))}
          >
            {INTERACTION_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="grid-2">
        <div className="field">
          <label>Date</label>
          <input type="date" value={state.date}
                 onChange={(e) => dispatch(setField({ field: 'date', value: e.target.value }))} />
        </div>
        <div className="field">
          <label>Time</label>
          <input type="time" value={state.time}
                 onChange={(e) => dispatch(setField({ field: 'time', value: e.target.value }))} />
        </div>
      </div>

      <div className="field">
        <label>Attendees</label>
        <div className="attendee-input-row">
          <input
            placeholder="Enter names or search..."
            value={attendeeInput}
            onChange={(e) => setAttendeeInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && attendeeInput.trim()) {
                dispatch(addAttendee(attendeeInput.trim()))
                setAttendeeInput('')
              }
            }}
          />
        </div>
        <ul className="chip-list">
          {state.attendees.map((a) => (
            <li key={a} className="chip removable">
              {a} <button onClick={() => dispatch(removeAttendee(a))}>×</button>
            </li>
          ))}
        </ul>
      </div>

      <div className="field">
        <label>Topics Discussed</label>
        <textarea
          placeholder="Enter key discussion points..."
          value={state.topicsDiscussed}
          onChange={(e) => dispatch(setField({ field: 'topicsDiscussed', value: e.target.value }))}
        />
      </div>

      <button type="button" className="secondary-btn">
        🎙️ Summarize from Voice Note (Requires Consent)
      </button>

      <MaterialsSamples />

      <div className="field">
        <label>Observed/Inferred HCP Sentiment</label>
        <SentimentSelector />
      </div>

      <div className="field">
        <label>Outcomes</label>
        <textarea
          placeholder="Key outcomes or agreements..."
          value={state.outcomes}
          onChange={(e) => dispatch(setField({ field: 'outcomes', value: e.target.value }))}
        />
      </div>

      <div className="field">
        <label>Follow-up Actions</label>
        <textarea
          placeholder="Enter next steps or tasks..."
          value={state.followUpActions}
          onChange={(e) => dispatch(setField({ field: 'followUpActions', value: e.target.value }))}
        />
      </div>

      {state.suggestedFollowUps.length > 0 && (
        <div className="ai-suggestions">
          <div className="field-label">AI Suggested Follow-ups:</div>
          <ul>
            {state.suggestedFollowUps.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      <div className="form-actions">
        <button
          type="button"
          className="primary-btn"
          disabled={state.status === 'saving'}
          onClick={() => dispatch(saveInteraction())}
        >
          {state.status === 'saving' ? 'Saving…' : 'Save Interaction'}
        </button>
        {state.status === 'saved' && <span className="save-status ok">Saved ✓</span>}
        {state.status === 'error' && <span className="save-status error">{state.error}</span>}
      </div>
    </div>
  )
}
