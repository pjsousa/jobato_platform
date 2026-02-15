import type { ResultRecord } from '../api/results-api'
import './ResultDetail.css'

type ResultDetailProps = {
  selectedResult: ResultRecord | null
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

const ResultDetails = ({ item }: { item: ResultRecord }) => (
  <div className="result-details">
    <h3>{item.title ?? '(Untitled result)'}</h3>
    <p>{item.snippet ?? 'No snippet available.'}</p>
    <dl>
      <div>
        <dt>Run</dt>
        <dd>{item.runId}</dd>
      </div>
      <div>
        <dt>Domain</dt>
        <dd>{item.domain ?? 'Unknown'}</dd>
      </div>
      <div>
        <dt>Created</dt>
        <dd>{item.createdAt ?? 'Unknown'}</dd>
      </div>
      <div>
        <dt>Final URL</dt>
        <dd>{item.finalUrl ?? 'N/A'}</dd>
      </div>
    </dl>
  </div>
)
