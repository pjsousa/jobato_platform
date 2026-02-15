import type { ResultRecord } from '../api/results-api'
import './ResultsList.css'

type ResultsListProps = {
  results: ResultRecord[]
  selectedResultId: number | null
  onSelectResult: (id: number) => void
  isLoading: boolean
  isEmpty: boolean
  errorMessage: string | null
  emptyStateMessage: string
}

export const ResultsList = ({
  results,
  selectedResultId,
  onSelectResult,
  isLoading,
  isEmpty,
  errorMessage,
  emptyStateMessage,
}: ResultsListProps) => (
  <article className="card">
    <h2>Result list</h2>
    {isLoading ? <p className="results-state">Loading results...</p> : null}
    {errorMessage ? <p className="results-error">{errorMessage}</p> : null}
    {isEmpty ? <p className="results-state">{emptyStateMessage}</p> : null}
    {!isLoading && !isEmpty ? (
      <ul className="results-list">
        {results.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`results-item${selectedResultId === item.id ? ' selected' : ''}`}
              onClick={() => onSelectResult(item.id)}
            >
              <span className="results-item__title">{item.title ?? '(Untitled result)'}</span>
              <span className="results-item__meta">{item.domain ?? 'Unknown domain'}</span>
            </button>
          </li>
        ))}
      </ul>
    ) : null}
  </article>
)
