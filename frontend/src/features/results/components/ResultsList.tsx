import type { ResultDisplayRecord } from '../api/results-api'
import './ResultsList.css'

const getManualLabelDisplay = (label: ResultDisplayRecord['manualLabel']) => {
  if (label === 'relevant') {
    return { text: 'Relevant', className: 'relevant' }
  }
  if (label === 'irrelevant') {
    return { text: 'Irrelevant', className: 'irrelevant' }
  }
  return null
}

type ResultsListProps = {
  results: ResultDisplayRecord[]
  selectedResultId: number | null
  onSelectResult: (id: number) => void
  isLoading: boolean
  isEmpty: boolean
  errorMessage: string | null
  emptyStateMessage: string
  hiddenIrrelevantCount: number
  showIrrelevant: boolean
}

export const ResultsList = ({
  results,
  selectedResultId,
  onSelectResult,
  isLoading,
  isEmpty,
  errorMessage,
  emptyStateMessage,
  hiddenIrrelevantCount,
  showIrrelevant,
}: ResultsListProps) => (
  <article className="card">
    <h2>Result list ({results.length})</h2>
    {!showIrrelevant && hiddenIrrelevantCount > 0 ? (
      <p className="results-state">{hiddenIrrelevantCount} irrelevant result(s) hidden.</p>
    ) : null}
    {isLoading ? <p className="results-state">Loading results...</p> : null}
    {errorMessage ? <p className="results-error">{errorMessage}</p> : null}
    {isEmpty ? <p className="results-state">{emptyStateMessage}</p> : null}
    {!isLoading && !isEmpty ? (
      <ul className="results-list">
        {results.map((item) => {
          const manualLabel = getManualLabelDisplay(item.manualLabel)
          return (
            <li key={item.id}>
              <button
                type="button"
                className={`results-item${selectedResultId === item.id ? ' selected' : ''}${
                  item.manualLabel === 'irrelevant' ? ' results-item--irrelevant' : ''
                }`}
                onClick={() => onSelectResult(item.id)}
              >
                <span className="results-item__title-row">
                  <span className="results-item__title">{item.title}</span>
                  {manualLabel ? (
                    <span className={`manual-label-pill manual-label-pill--${manualLabel.className}`}>
                      {manualLabel.text}
                    </span>
                  ) : null}
                  {item.duplicateCount > 0 ? (
                    <span className="results-item__duplicate-badge">{item.duplicateCount} duplicate(s)</span>
                  ) : null}
                </span>
                <span className="results-item__company">{item.company}</span>
                <span className="results-item__snippet">{item.snippet}</span>
                <span className="results-item__meta">
                  <span>{item.source}</span>
                  <span aria-hidden="true">•</span>
                  <span>{item.postedDate}</span>
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    ) : null}
  </article>
)
