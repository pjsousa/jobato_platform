import { type FormEvent, useState } from 'react'
import { ApiError, type Query } from '../api/queries'
import { useCreateQuery, useQueries, useUpdateQuery } from '../hooks/use-queries'
import './QueryManager.css'

const getErrorMessage = (error: unknown) => {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong. Please try again.'
}

const formatTimestamp = (value: string) => {
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

export const QueryManager = () => {
  const { data: queries = [], isLoading, isError, error } = useQueries()
  const createQuery = useCreateQuery()
  const updateQuery = useUpdateQuery()

  const [newText, setNewText] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingText, setEditingText] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const startEditing = (query: Query) => {
    setEditingId(query.id)
    setEditingText(query.text)
    setFormError(null)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditingText('')
  }

  const handleAdd = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = newText.trim()
    if (!trimmed) {
      setFormError('Enter a query before saving.')
      return
    }

    createQuery.mutate(trimmed, {
      onSuccess: () => {
        setNewText('')
        setFormError(null)
      },
      onError: (err: unknown) => setFormError(getErrorMessage(err)),
    })
  }

  const handleUpdate = (id: string, update: { text?: string; enabled?: boolean }) => {
    updateQuery.mutate(
      { id, update },
      {
        onSuccess: () => {
          setFormError(null)
          cancelEditing()
        },
        onError: (err: unknown) => setFormError(getErrorMessage(err)),
      },
    )
  }

  return (
    <section className="query-manager">
      <div className="query-form">
        <div className="query-form__header">
          <h2>Manage query inputs</h2>
          <p>Keep the list lean. Each entry fuels future runs only.</p>
        </div>
        <form className="query-form__controls" onSubmit={handleAdd}>
          <input
            className="query-input"
            type="text"
            placeholder="e.g. senior product designer remote"
            value={newText}
            onChange={(event) => setNewText(event.target.value)}
          />
          <button className="button primary" type="submit" disabled={createQuery.isPending}>
            Add query
          </button>
        </form>
        {formError ? <p className="query-form__error">{formError}</p> : null}
      </div>

      <div className="query-list">
        {isLoading ? <p className="query-status">Loading queries...</p> : null}
        {isError ? (
          <p className="query-status error">{getErrorMessage(error)}</p>
        ) : null}
        {!isLoading && queries.length === 0 ? (
          <p className="query-status">No queries saved yet. Add your first one above.</p>
        ) : null}

        {queries.map((query, index) => {
          const isEditing = editingId === query.id
          return (
            <div
              key={query.id}
              className={`query-card ${query.enabled ? '' : 'is-disabled'}`}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className="query-main">
                <span className={`query-pill ${query.enabled ? 'enabled' : 'disabled'}`}>
                  {query.enabled ? 'Enabled' : 'Disabled'}
                </span>
                {isEditing ? (
                  <input
                    className="query-edit-input"
                    value={editingText}
                    onChange={(event) => setEditingText(event.target.value)}
                  />
                ) : (
                  <h3 className="query-title">{query.text}</h3>
                )}
                <span className="query-meta">Updated {formatTimestamp(query.updatedAt)}</span>
              </div>
              <div className="query-actions">
                {isEditing ? (
                  <div className="query-edit">
                    <button
                      className="button primary"
                      type="button"
                      onClick={() => handleUpdate(query.id, { text: editingText })}
                      disabled={updateQuery.isPending}
                    >
                      Save
                    </button>
                    <button className="button secondary" type="button" onClick={cancelEditing}>
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      className="button ghost"
                      type="button"
                      onClick={() => startEditing(query)}
                      disabled={updateQuery.isPending}
                    >
                      Edit
                    </button>
                    <button
                      className="button secondary"
                      type="button"
                      onClick={() => handleUpdate(query.id, { enabled: !query.enabled })}
                      disabled={updateQuery.isPending}
                    >
                      {query.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
