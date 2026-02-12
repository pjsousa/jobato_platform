import type { RunResponse } from '../api/runs-api'
import type { RunSummaryResponse } from '../../reports/api/reports-api'
import './RunStatus.css'

type RunStatusProps = {
  run?: RunResponse | null
  summary?: RunSummaryResponse | null
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

const formatCount = (value?: number | null) => {
  if (value === null || value === undefined) {
    return '—'
  }
  return new Intl.NumberFormat().format(value)
}

const formatDuration = (value?: number | null) => {
  if (value === null || value === undefined || value < 0) {
    return '—'
  }
  if (value < 1000) {
    return `${value} ms`
  }
  const totalSeconds = Math.floor(value / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${totalSeconds}s`
}

const RunSummaryBar = ({ run, summary }: { run?: RunResponse | null; summary?: RunSummaryResponse | null }) => {
  const summaryStatus = run?.status ?? summary?.status

  return (
  <div className="run-summary">
    <div className="run-summary__item">
      <span className="run-summary__label">Last run</span>
      <span className="run-summary__value">{formatTimestamp(summary?.triggerTime ?? run?.startedAt)}</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">Duration</span>
      <span className="run-summary__value">{formatDuration(summary?.durationMs)}</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">New count</span>
      <span className="run-summary__value">{formatCount(summary?.newJobsCount)}</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">Relevant count</span>
      <span className="run-summary__value">{formatCount(summary?.relevantCount)}</span>
    </div>
    <div className="run-summary__item">
      <span className="run-summary__label">Status</span>
      <span className={`run-summary__value ${summaryStatus === 'partial' ? 'is-warning' : ''}`}>
        {summaryStatus ? (statusLabelMap[summaryStatus] ?? summaryStatus) : '—'}
      </span>
    </div>
  </div>
  )
}

export const RunStatus = ({ run, summary, isLoading = false, errorMessage }: RunStatusProps) => {
  const status = run?.status ?? summary?.status ?? 'unknown'
  const statusLabel = statusLabelMap[status] ?? status
  const statusClass = statusClassMap[status] ?? 'is-unknown'
  const quotaReached = run?.status === 'partial' && run?.statusReason === 'quota-reached'
  const statusNotice = errorMessage ?? (quotaReached ? 'Quota reached mid-run. Results are partial.' : null)

  return (
    <div className="run-status">
      <div className="run-status__header">
        <div>
          <h2>Run status</h2>
          <p>Track the latest run state and timing.</p>
        </div>
        {run || summary ? (
          <span className={`run-status-pill ${statusClass}`}>{statusLabel}</span>
        ) : null}
      </div>

      <RunSummaryBar run={run} summary={summary} />

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

      {statusNotice ? (
        <div className="run-status__banner warning">
          <strong>Status notice</strong>
          <span>{statusNotice}</span>
        </div>
      ) : null}
    </div>
  )
}
