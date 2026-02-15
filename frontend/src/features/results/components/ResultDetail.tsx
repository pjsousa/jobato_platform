import type { ResultDisplayRecord } from '../api/results-api'
import './ResultDetail.css'

type ResultDetailProps = {
  selectedResult: ResultDisplayRecord | null
  isLoading: boolean
  isEmpty: boolean
}

export const ResultDetail = ({ selectedResult, isLoading, isEmpty }: ResultDetailProps) => (
  <article className="card">
    <h2>Details</h2>
    {isLoading ? <p className="results-state">Loading result details...</p> : null}
    {!isLoading && isEmpty ? <p className="results-state">No result selected yet.</p> : null}
    {!isLoading && !isEmpty && !selectedResult ? (
      <p className="results-state">Select a result to inspect details.</p>
    ) : null}
    {selectedResult ? <ResultDetails item={selectedResult} /> : null}
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

const ResultDetails = ({ item }: { item: ResultDisplayRecord }) => (
  <div className="result-details">
    <h3>{item.title}</h3>
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
