import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { getFeedbackErrorMessage, useFeedback } from '../../feedback'
import { ApiError, type ManualLabel, type ResultDisplayRecord, type ResultsView } from '../api/results-api'
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

const getNextManualLabel = (label: ManualLabel): ManualLabel => {
  if (label === null) {
    return 'relevant'
  }
  if (label === 'relevant') {
    return 'irrelevant'
  }
  return null
}

export const ResultsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const view = resolveView(searchParams.get('view'))
  const showIrrelevant = searchParams.get('showIrrelevant') === 'true'

  useEffect(() => {
    if (searchParams.get('view') !== view) {
      const nextParams = new URLSearchParams(searchParams)
      nextParams.set('view', view)
      setSearchParams(nextParams, { replace: true })
    }
  }, [searchParams, setSearchParams, view])

  const { data, isLoading, isFetching, error } = useResults(view)
  const feedbackMutation = useFeedback()
  const results: ResultDisplayRecord[] = data ?? []
  const visibleResults = useMemo(
    () => (showIrrelevant ? results : results.filter((item) => item.manualLabel !== 'irrelevant')),
    [results, showIrrelevant],
  )
  const hiddenIrrelevantCount = results.length - visibleResults.length
  const [selectedId, setSelectedId] = useState<number | null>(null)

  useEffect(() => {
    if (visibleResults.length === 0) {
      setSelectedId(null)
      return
    }

    setSelectedId((previous) => {
      if (previous != null && visibleResults.some((item) => item.id === previous)) {
        return previous
      }

      if (previous != null) {
        const previousIndex = results.findIndex((item) => item.id === previous)
        if (previousIndex >= 0) {
          const nextVisible = results
            .slice(previousIndex + 1)
            .find((item) => showIrrelevant || item.manualLabel !== 'irrelevant')
          if (nextVisible) {
            return nextVisible.id
          }
        }
      }

      return visibleResults[0].id
    })
  }, [results, showIrrelevant, visibleResults])

  const selectedItem = useMemo(() => {
    if (selectedId == null) {
      return null
    }
    return visibleResults.find((item) => item.id === selectedId) ?? null
  }, [selectedId, visibleResults])

  const showInitialLoading = isLoading && results.length === 0
  const isUpdating = isFetching && !showInitialLoading
  const isEmpty = !showInitialLoading && visibleResults.length === 0

  const emptyStateMessage =
    view === 'today'
      ? 'No results in today\'s run yet.'
      : 'No results found across all runs yet.'

  const changeView = (nextView: ResultsView) => {
    if (nextView === view) {
      return
    }
    setSearchParams((previousParams) => {
      const nextParams = new URLSearchParams(previousParams)
      nextParams.set('view', nextView)
      return nextParams
    })
  }

  const changeShowIrrelevant = (nextValue: boolean) => {
    setSearchParams((previousParams) => {
      const nextParams = new URLSearchParams(previousParams)
      if (nextValue) {
        nextParams.set('showIrrelevant', 'true')
      } else {
        nextParams.delete('showIrrelevant')
      }
      return nextParams
    })
  }

  const handleCycleManualLabel = () => {
    if (!selectedItem || feedbackMutation.isPending) {
      return
    }

    const nextLabel = getNextManualLabel(selectedItem.manualLabel)
    feedbackMutation.mutate({
      resultId: selectedItem.id,
      label: nextLabel,
    })
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
        <label className="results-toggle" htmlFor="show-irrelevant-toggle">
          <input
            id="show-irrelevant-toggle"
            type="checkbox"
            checked={showIrrelevant}
            onChange={(event) => changeShowIrrelevant(event.currentTarget.checked)}
          />
          Show irrelevant
        </label>
        {isUpdating ? <span className="results-updating">Updating results...</span> : null}
      </section>

      <section className="results-grid">
        <ResultsList
          results={visibleResults}
          selectedResultId={selectedId}
          onSelectResult={setSelectedId}
          isLoading={showInitialLoading}
          isEmpty={isEmpty}
          errorMessage={error && !showInitialLoading ? getErrorMessage(error) : null}
          emptyStateMessage={emptyStateMessage}
          hiddenIrrelevantCount={hiddenIrrelevantCount}
          showIrrelevant={showIrrelevant}
        />
        <ResultDetail
          selectedResult={selectedItem}
          isLoading={showInitialLoading}
          isEmpty={isEmpty}
          onCycleManualLabel={handleCycleManualLabel}
          isFeedbackPending={feedbackMutation.isPending}
          feedbackErrorMessage={feedbackMutation.isError ? getFeedbackErrorMessage(feedbackMutation.error) : null}
        />
      </section>
    </div>
  )
}
