import type { ChangeEvent, FormEvent } from 'react'
import { useState } from 'react'

type AllowlistFormProps = {
  mode: 'create' | 'edit'
  initialDomain?: string
  onSubmit: (domain: string) => void
  onCancel?: () => void
  isSubmitting: boolean
  error?: string | null
}

export const AllowlistForm = ({
  mode,
  initialDomain,
  onSubmit,
  onCancel,
  isSubmitting,
  error,
}: AllowlistFormProps) => {
  const [domain, setDomain] = useState(initialDomain ?? '')

  const submitLabel = mode === 'create' ? 'Add domain' : 'Save changes'

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = domain.trim()
    if (!trimmed) {
      return
    }
    onSubmit(trimmed)
  }

  return (
    <form className="allowlist-form" onSubmit={handleSubmit}>
      <label className="allowlist-label" htmlFor="allowlist-domain">
        Domain
      </label>
      <input
        id="allowlist-domain"
        name="domain"
        className="allowlist-input"
        placeholder="example.com"
        value={domain}
        onChange={(event: ChangeEvent<HTMLInputElement>) => setDomain(event.target.value)}
        autoComplete="off"
      />
      <p className="allowlist-help">
        Enter a domain only (no scheme, path, or port).
      </p>
      {error ? <p className="allowlist-error">{error}</p> : null}
      <div className="allowlist-actions">
        <button className="button primary" type="submit" disabled={isSubmitting || !domain.trim()}>
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
        {mode === 'edit' && onCancel ? (
          <button className="button ghost" type="button" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  )
}
