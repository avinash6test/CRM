import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { addMaterial, addSample } from '../store/interactionSlice'

export default function MaterialsSamples() {
  const dispatch = useDispatch()
  const { materialsShared, samplesDistributed } = useSelector((s) => s.interaction)
  const [materialInput, setMaterialInput] = useState('')
  const [sampleInput, setSampleInput] = useState('')

  return (
    <div>
      <h3 className="section-label">Materials Shared / Samples Distributed</h3>

      <div className="material-row">
        <div>
          <div className="field-label">Materials Shared</div>
          {materialsShared.length === 0 ? (
            <div className="empty-hint">No materials added.</div>
          ) : (
            <ul className="chip-list">
              {materialsShared.map((m, i) => <li key={i} className="chip">{m}</li>)}
            </ul>
          )}
        </div>
        <div className="add-control">
          <input
            placeholder="Search material…"
            value={materialInput}
            onChange={(e) => setMaterialInput(e.target.value)}
          />
          <button
            type="button"
            onClick={() => {
              if (materialInput.trim()) {
                dispatch(addMaterial(materialInput.trim()))
                setMaterialInput('')
              }
            }}
          >
            🔍 Search/Add
          </button>
        </div>
      </div>

      <div className="material-row">
        <div>
          <div className="field-label">Samples Distributed</div>
          {samplesDistributed.length === 0 ? (
            <div className="empty-hint">No samples added.</div>
          ) : (
            <ul className="chip-list">
              {samplesDistributed.map((s, i) => <li key={i} className="chip">{s}</li>)}
            </ul>
          )}
        </div>
        <div className="add-control">
          <input
            placeholder="Sample name…"
            value={sampleInput}
            onChange={(e) => setSampleInput(e.target.value)}
          />
          <button
            type="button"
            onClick={() => {
              if (sampleInput.trim()) {
                dispatch(addSample(sampleInput.trim()))
                setSampleInput('')
              }
            }}
          >
            📦 Add Sample
          </button>
        </div>
      </div>
    </div>
  )
}
