import { useEffect, useRef, type KeyboardEvent } from 'react'

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
}: ResultsListProps) => {
  const listRef = useRef<HTMLUListElement | null>(null)
  const optionRefs = useRef<Record<number, HTMLLIElement | null>>({})

  useEffect(() => {
    if (selectedResultId == null) {
      return
    }

    const activeOption = optionRefs.current[selectedResultId]
    if (!activeOption || typeof activeOption.scrollIntoView !== 'function') {
      return
    }

    activeOption.scrollIntoView({ block: 'nearest' })
  }, [selectedResultId])

  const selectByIndex = (index: number) => {
    if (results.length === 0) {
      return
    }

    const boundedIndex = Math.max(0, Math.min(index, results.length - 1))
    onSelectResult(results[boundedIndex].id)
  }

  const handleListKeyDown = (event: KeyboardEvent<HTMLUListElement>) => {
    if (results.length === 0) {
      return
    }

    const selectedIndex = selectedResultId == null ? -1 : results.findIndex((item) => item.id === selectedResultId)

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (selectedIndex < 0) {
        selectByIndex(0)
      } else {
        selectByIndex(selectedIndex + 1)
      }
      return
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      if (selectedIndex < 0) {
        selectByIndex(results.length - 1)
      } else {
        selectByIndex(selectedIndex - 1)
      }
      return
    }

    if (event.key === 'Home') {
      event.preventDefault()
      selectByIndex(0)
      return
    }

    if (event.key === 'End') {
      event.preventDefault()
      selectByIndex(results.length - 1)
    }
  }

  const handleOptionClick = (id: number) => {
    onSelectResult(id)
    listRef.current?.focus()
  }

  const activeDescendantId = selectedResultId == null ? undefined : `results-option-${selectedResultId}`

  return (
    <article className="card">
      <h2>Result list ({results.length})</h2>
      {!showIrrelevant && hiddenIrrelevantCount > 0 ? (
        <p className="results-state">{hiddenIrrelevantCount} irrelevant result(s) hidden.</p>
      ) : null}
      {isLoading ? <p className="results-state">Loading results...</p> : null}
      {errorMessage ? <p className="results-error">{errorMessage}</p> : null}
      {isEmpty ? <p className="results-state">{emptyStateMessage}</p> : null}
      {!isLoading && !isEmpty ? (
        <ul
          ref={listRef}
          className="results-list"
          role="listbox"
          aria-label="Search results"
          aria-activedescendant={activeDescendantId}
          tabIndex={0}
          onKeyDown={handleListKeyDown}
        >
          {results.map((item) => {
            const manualLabel = getManualLabelDisplay(item.manualLabel)
            return (
              <li
                key={item.id}
                id={`results-option-${item.id}`}
                role="option"
                aria-selected={selectedResultId === item.id}
                className={`results-item${selectedResultId === item.id ? ' selected' : ''}${
                  item.manualLabel === 'irrelevant' ? ' results-item--irrelevant' : ''
                }`}
                ref={(node) => {
                  optionRefs.current[item.id] = node
                }}
              >
                <button
                  type="button"
                  tabIndex={-1}
                  className="results-item__button"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => handleOptionClick(item.id)}
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
}
