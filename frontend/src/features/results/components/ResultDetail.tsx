import type { KeyboardEvent } from 'react'

import type { ResultDisplayRecord } from '../api/results-api'
import './ResultDetail.css'

type ResultDetailProps = {
  selectedResult: ResultDisplayRecord | null
  isLoading: boolean
  isEmpty: boolean
  onCycleManualLabel: () => void
  isFeedbackPending: boolean
  feedbackErrorMessage: string | null
}

const getManualLabelDisplay = (label: ResultDisplayRecord['manualLabel']) => {
  if (label === 'relevant') {
    return { text: 'Relevant', className: 'relevant' }
  }
  if (label === 'irrelevant') {
    return { text: 'Irrelevant', className: 'irrelevant' }
  }
  return null
}

export const ResultDetail = ({
  selectedResult,
  isLoading,
  isEmpty,
  onCycleManualLabel,
  isFeedbackPending,
  feedbackErrorMessage,
}: ResultDetailProps) => (
  <article className="card">
    <h2>Details</h2>
    {isLoading ? <p className="results-state">Loading result details...</p> : null}
    {!isLoading && isEmpty ? <p className="results-state">No result selected yet.</p> : null}
    {!isLoading && !isEmpty && !selectedResult ? (
      <p className="results-state">Select a result to inspect details.</p>
    ) : null}
    {feedbackErrorMessage ? <p className="results-error">{feedbackErrorMessage} Please try again.</p> : null}
    {selectedResult ? (
      <ResultDetails item={selectedResult} onCycleManualLabel={onCycleManualLabel} isFeedbackPending={isFeedbackPending} />
    ) : null}
  </article>
)

const getCanonicalContext = (item: ResultDisplayRecord) => {
  if (item.isDuplicate) {
    if (item.canonicalId != null) {
      return `This result is marked as a duplicate of canonical result #${item.canonicalId}.`
    }
    return 'This result is marked as a duplicate, but the canonical result is unavailable.'
  }

  if (item.duplicateCount > 0) {
    return `This is the canonical result for ${item.duplicateCount} duplicate(s).`
  }

  return 'This result is currently the canonical record with no linked duplicates.'
}

const ResultDetails = ({
  item,
  onCycleManualLabel,
  isFeedbackPending,
}: {
  item: ResultDisplayRecord
  onCycleManualLabel: () => void
  isFeedbackPending: boolean
}) => {
  const manualLabel = getManualLabelDisplay(item.manualLabel)
  const handleTitleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Space' || event.key === 'Spacebar') {
      event.preventDefault()
      onCycleManualLabel()
    }
  }

  return (
    <div className={`result-details${item.manualLabel === 'irrelevant' ? ' result-details--irrelevant' : ''}`}>
      <div className="result-details__title-row">
        <button
          type="button"
          className="result-details__title-button"
          onClick={onCycleManualLabel}
          onKeyDown={handleTitleKeyDown}
          disabled={isFeedbackPending}
          aria-label="Cycle manual feedback label"
        >
          <h3>{item.title}</h3>
        </button>
        {manualLabel ? <span className={`manual-label-pill manual-label-pill--${manualLabel.className}`}>{manualLabel.text}</span> : null}
      </div>
      <p>{item.snippet}</p>
      <p className="result-details__canonical-context">{getCanonicalContext(item)}</p>
      <dl>
      <div>
        <dt>Company</dt>
        <dd>{item.company}</dd>
      </div>
      <div>
        <dt>Source</dt>
        <dd>{item.source}</dd>
      </div>
      <div>
        <dt>Posted</dt>
        <dd>{item.postedDate}</dd>
      </div>
      <div>
        <dt>Duplicate count</dt>
        <dd>{item.duplicateCount}</dd>
      </div>
      <div>
        <dt>Run</dt>
        <dd>{item.runId}</dd>
      </div>
      <div>
        <dt>Canonical ID</dt>
        <dd>{item.canonicalId ?? 'N/A'}</dd>
      </div>
      <div>
        <dt>Source link</dt>
        <dd>
          {item.sourceUrl ? (
            <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">
              Open source page
            </a>
          ) : (
            'N/A'
          )}
        </dd>
      </div>
      </dl>
    </div>
  )
}
