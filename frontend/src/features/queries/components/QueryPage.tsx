import { QueryManager } from './QueryManager'
import './QueryPage.css'

export const QueryPage = () => (
  <div className="page query-page">
    <header className="page-header query-hero">
      <span className="eyebrow">Search scope</span>
      <h1>Query strings for future runs</h1>
      <p className="subtitle">
        Capture the queries you care about. Updates apply to new runs only and never alter historical
        results.
      </p>
    </header>

    <section className="card query-panel">
      <QueryManager />
    </section>

    <footer className="query-hint">
      Saved to <strong>config/queries.yaml</strong> and shared with the API and ML pipeline.
    </footer>
  </div>
)
