import type { RunResponse } from '../api/runs-api'
import './RunStatus.css'

type RunStatusProps = {
  run?: RunResponse | null
  isLoading?: boolean
  errorMessage?: string | null
}

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return '—'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const statusLabelMap: Record<string, string> = {
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  partial: 'Partial',
}

const statusClassMap: Record<string, string> = {
  running: 'is-running',
  completed: 'is-completed',
  failed: 'is-failed',
  partial: 'is-partial',
}

const RunSummaryBar = ({ run }: { run?: RunResponse | null }) => (
  <div className="run-summary">
    <div className="run-summary__item">
      <span className="run-summary__label">Last run</span>
      <span className="run-summary__value">{formatTimestamp(run?.startedAt)}</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">New count</span>
      <span className="run-summary__value">—</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">Relevant count</span>
      <span className="run-summary__value">—</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">Quota remaining</span>
      <span className="run-summary__value">—</span>
    </div>
  </div>
)

export const RunStatus = ({ run, isLoading = false, errorMessage }: RunStatusProps) => {
  const status = run?.status ?? 'unknown'
  const statusLabel = statusLabelMap[status] ?? status
  const statusClass = statusClassMap[status] ?? 'is-unknown'

  return (
    <div className="run-status">
      <div className="run-status__header">
        <div>
          <h2>Run status</h2>
          <p>Track the latest run state and timing.</p>
        </div>
        {run ? (
          <span className={`run-status-pill ${statusClass}`}>{statusLabel}</span>
        ) : null}
      </div>

      <RunSummaryBar run={run} />

      <div className="run-status__details">
        {isLoading ? <p className="run-status__empty">Loading run status…</p> : null}
        {!isLoading && !run ? <p className="run-status__empty">No runs yet. Trigger one to begin.</p> : null}
        {run ? (
          <>
            <div className="run-status__row">
              <span className="run-status__label">Run ID</span>
              <span className="run-status__value">{run.runId}</span>
            </div>
            <div className="run-status__row">
              <span className="run-status__label">Started</span>
              <span className="run-status__value">{formatTimestamp(run.startedAt)}</span>
            </div>
            <div className="run-status__row">
              <span className="run-status__label">Ended</span>
              <span className="run-status__value">{formatTimestamp(run.endedAt)}</span>
            </div>
          </>
        ) : null}
      </div>

      {errorMessage ? (
        <div className="run-status__banner warning">
          <strong>Status notice</strong>
          <span>{errorMessage}</span>
        </div>
      ) : null}
    </div>
  )
}
