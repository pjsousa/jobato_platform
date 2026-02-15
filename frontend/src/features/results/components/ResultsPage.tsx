import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { ApiError, type ResultDisplayRecord, type ResultsView } from '../api/results-api'
import { useResults } from '../hooks/use-results'
import { ResultDetail } from './ResultDetail'
import { ResultsList } from './ResultsList'
import './ResultsPage.css'

const resolveView = (rawValue: string | null): ResultsView =>
  rawValue === 'all-time' ? 'all-time' : 'today'

const getErrorMessage = (error: unknown) => {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unable to load results right now.'
}

export const ResultsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const view = resolveView(searchParams.get('view'))

  useEffect(() => {
    if (searchParams.get('view') !== view) {
      const nextParams = new URLSearchParams(searchParams)
      nextParams.set('view', view)
      setSearchParams(nextParams, { replace: true })
    }
  }, [searchParams, setSearchParams, view])

  const { data, isLoading, isFetching, error } = useResults(view)
  const results: ResultDisplayRecord[] = data ?? []
  const [selectedId, setSelectedId] = useState<number | null>(null)

  useEffect(() => {
    if (results.length === 0) {
      setSelectedId(null)
      return
    }

    setSelectedId((previous) => {
      if (previous != null && results.some((item) => item.id === previous)) {
        return previous
      }
      return results[0].id
    })
  }, [results])

  const selectedItem = useMemo(() => {
    if (selectedId == null) {
      return null
    }
    return results.find((item) => item.id === selectedId) ?? null
  }, [results, selectedId])

  const showInitialLoading = isLoading && results.length === 0
  const isUpdating = isFetching && !showInitialLoading
  const isEmpty = !showInitialLoading && results.length === 0

  const emptyStateMessage =
    view === 'today'
      ? 'No results in today\'s run yet.'
      : 'No results found across all runs yet.'

  const changeView = (nextView: ResultsView) => {
    if (nextView === view) {
      return
    }
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('view', nextView)
    setSearchParams(nextParams)
  }

  return (
    <div className="page results-page">
      <header className="page-header results-hero">
        <span className="eyebrow">Result review</span>
        <h1>Collected search results</h1>
        <p className="subtitle">Switch between the latest run and all captured history.</p>
      </header>

      <section className="card results-toolbar">
        <div className="results-tabs" role="tablist" aria-label="Results view">
          <button
            type="button"
            role="tab"
            aria-selected={view === 'today'}
            className={`results-tab${view === 'today' ? ' active' : ''}`}
            onClick={() => changeView('today')}
          >
            Today
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === 'all-time'}
            className={`results-tab${view === 'all-time' ? ' active' : ''}`}
            onClick={() => changeView('all-time')}
          >
            All Time
          </button>
        </div>
        {isUpdating ? <span className="results-updating">Updating results...</span> : null}
      </section>

      <section className="results-grid">
        <ResultsList
          results={results}
          selectedResultId={selectedId}
          onSelectResult={setSelectedId}
          isLoading={showInitialLoading}
          isEmpty={isEmpty}
          errorMessage={error && !showInitialLoading ? getErrorMessage(error) : null}
          emptyStateMessage={emptyStateMessage}
        />
        <ResultDetail selectedResult={selectedItem} isLoading={showInitialLoading} isEmpty={isEmpty} />
      </section>
    </div>
  )
}
