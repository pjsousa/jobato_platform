import { useEffect, useState } from 'react'

import { ApiError, type RunResponse } from '../api/runs-api'
import { useLatestRunSummary } from '../../reports/hooks/use-reports'
import { useRun, useTriggerRun } from '../hooks/use-runs'
import { RunControls } from './RunControls'
import { RunStatus } from './RunStatus'
import './RunPage.css'

const STORAGE_KEY = 'jobato:lastRunId'

const resolveError = (error: unknown) => {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return null
}

export const RunPage = () => {
  const [runId, setRunId] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [statusNotice, setStatusNotice] = useState<string | null>(null)

  const triggerRun = useTriggerRun()
  const { data: run, isLoading, error: runError } = useRun(runId)
  const { data: latestSummary } = useLatestRunSummary()

  useEffect(() => {
    if (runId) {
      localStorage.setItem(STORAGE_KEY, runId)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [runId])

  const handleTrigger = () => {
    setStatusNotice(null)
    triggerRun.mutate(undefined, {
      onSuccess: (response: RunResponse) => {
        setRunId(response.runId)
        setStatusNotice(null)
      },
      onError: (error) => {
        setStatusNotice(resolveError(error))
      },
    })
  }

  const errorMessage = statusNotice ?? resolveError(runError)

  return (
    <div className="page run-page">
      <header className="page-header run-hero">
        <span className="eyebrow">Run orchestration</span>
        <h1>Manual run control</h1>
        <p className="subtitle">Kick off a run and monitor lifecycle state from one place.</p>
      </header>

      <section className="card">
        <RunControls
          onTrigger={handleTrigger}
          isRunning={run?.status === 'running'}
          isPending={triggerRun.isPending}
        />
      </section>

      <section className="card">
        <RunStatus run={run} summary={latestSummary} isLoading={isLoading} errorMessage={errorMessage} />
      </section>
    </div>
  )
}
