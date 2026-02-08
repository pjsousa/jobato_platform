import { useMemo, useState } from 'react'

import type { AllowlistEntry } from '../api/allowlist-api'
import { ApiError } from '../api/allowlist-api'
import { useAllowlists, useCreateAllowlist, useUpdateAllowlist } from '../hooks/use-allowlist'
import { AllowlistForm } from './AllowlistForm'
import { AllowlistTable } from './AllowlistTable'

export const AllowlistPage = () => {
  const { data, isLoading, error } = useAllowlists()
  const createMutation = useCreateAllowlist()
  const updateMutation = useUpdateAllowlist()

  const [editing, setEditing] = useState<AllowlistEntry | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const entries = useMemo(() => data ?? [], [data])

  const handleSubmit = async (domain: string) => {
    setFormError(null)
    try {
      if (editing) {
        await updateMutation.mutateAsync({
          currentDomain: editing.domain,
          update: { domain, enabled: editing.enabled },
        })
        setEditing(null)
        return
      }

      await createMutation.mutateAsync(domain)
    } catch (submissionError) {
      setFormError(resolveError(submissionError))
    }
  }

  const handleToggle = async (entry: AllowlistEntry, enabled: boolean) => {
    setFormError(null)
    try {
      await updateMutation.mutateAsync({
        currentDomain: entry.domain,
        update: { enabled },
      })
    } catch (toggleError) {
      setFormError(resolveError(toggleError))
    }
  }

  const handleEdit = (entry: AllowlistEntry) => {
    setFormError(null)
    setEditing(entry)
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Search Scope</p>
          <h1>Allowlist Domains</h1>
          <p className="subtitle">Only enabled domains are used for new runs.</p>
        </div>
        <div className="summary">
          <span>{entries.length} total</span>
          <span>{entries.filter((entry: AllowlistEntry) => entry.enabled).length} enabled</span>
        </div>
      </header>

      <section className="card">
        <h2>{editing ? 'Edit domain' : 'Add a domain'}</h2>
        <AllowlistForm
          key={editing?.domain ?? 'create'}
          mode={editing ? 'edit' : 'create'}
          initialDomain={editing?.domain}
          onSubmit={handleSubmit}
          onCancel={() => setEditing(null)}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
          error={formError}
        />
      </section>

      <section className="card">
        <div className="table-header">
          <h2>Current allowlist</h2>
          {isLoading ? <span className="status-pill">Loading...</span> : null}
        </div>
        {error ? <p className="allowlist-error">{resolveError(error)}</p> : null}
        <AllowlistTable entries={entries} onToggle={handleToggle} onEdit={handleEdit} />
      </section>
    </div>
  )
}

const resolveError = (error: unknown) => {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong'
}
