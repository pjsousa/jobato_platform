import type { AllowlistEntry } from '../api/allowlist-api'

type AllowlistTableProps = {
  entries: AllowlistEntry[]
  onToggle: (entry: AllowlistEntry, enabled: boolean) => void
  onEdit: (entry: AllowlistEntry) => void
}

export const AllowlistTable = ({ entries, onToggle, onEdit }: AllowlistTableProps) => {
  if (entries.length === 0) {
    return <p className="allowlist-empty">No allowlisted domains yet.</p>
  }

  return (
    <div className="allowlist-table">
      <div className="allowlist-row header">
        <span>Domain</span>
        <span>Status</span>
        <span>Actions</span>
      </div>
      {entries.map((entry) => (
        <div key={entry.domain} className="allowlist-row">
          <span className="domain">{entry.domain}</span>
          <span className={`status ${entry.enabled ? 'enabled' : 'disabled'}`}>
            {entry.enabled ? 'Enabled' : 'Disabled'}
          </span>
          <span className="actions">
            <button
              className="button ghost"
              type="button"
              onClick={() => onToggle(entry, !entry.enabled)}
              aria-label={`${entry.enabled ? 'Disable' : 'Enable'} ${entry.domain}`}
            >
              {entry.enabled ? 'Disable' : 'Enable'}
            </button>
            <button
              className="button ghost"
              type="button"
              onClick={() => onEdit(entry)}
              aria-label={`Edit ${entry.domain}`}
            >
              Edit
            </button>
          </span>
        </div>
      ))}
    </div>
  )
}
