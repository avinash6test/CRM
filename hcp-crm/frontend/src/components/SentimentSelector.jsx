import React from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setSentiment } from '../store/interactionSlice'

const OPTIONS = [
  { value: 'positive', label: 'Positive', emoji: '🙂' },
  { value: 'neutral', label: 'Neutral', emoji: '😐' },
  { value: 'negative', label: 'Negative', emoji: '🙁' },
]

export default function SentimentSelector() {
  const dispatch = useDispatch()
  const sentiment = useSelector((s) => s.interaction.sentiment)

  return (
    <div className="sentiment-row">
      {OPTIONS.map((opt) => (
        <label key={opt.value} className={`sentiment-option ${sentiment === opt.value ? 'active' : ''}`}>
          <input
            type="radio"
            name="sentiment"
            checked={sentiment === opt.value}
            onChange={() => dispatch(setSentiment(opt.value))}
          />
          <span className="sentiment-emoji">{opt.emoji}</span>
          <span>{opt.label}</span>
        </label>
      ))}
    </div>
  )
}
