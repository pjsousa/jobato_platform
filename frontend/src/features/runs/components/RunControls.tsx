import './RunControls.css'

type RunControlsProps = {
  onTrigger: () => void
  isRunning: boolean
  isPending: boolean
}

export const RunControls = ({ onTrigger, isRunning, isPending }: RunControlsProps) => (
  <div className="run-controls">
    <div className="run-controls__copy">
      <h2>Trigger a new run</h2>
      <p>
        Start the search pipeline when your allowlist and queries are ready. The run will lock until
        completion so results stay consistent.
      </p>
    </div>
    <div className="run-controls__actions">
      <button
        className="button primary"
        type="button"
        onClick={onTrigger}
        disabled={isPending || isRunning}
      >
        {isRunning ? 'Run in progress' : 'Start run'}
      </button>
      <span className="run-controls__status">
        {isPending ? 'Submitting run request…' : 'Runs publish updates via Redis Streams.'}
      </span>
    </div>
  </div>
)
