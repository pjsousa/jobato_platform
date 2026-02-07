import './App.css'
import { QueryManager } from './features/queries/components/QueryManager'

function App() {
  return (
    <div className="app">
      <header className="hero">
        <span className="eyebrow">Search scope</span>
        <h1>Query strings for future runs</h1>
        <p>
          Capture the queries you care about. Updates apply to new runs only and
          never alter historical results.
        </p>
      </header>
      <main className="panel">
        <QueryManager />
      </main>
      <footer className="hint">
        Saved to <strong>config/queries.yaml</strong> and shared with the API and
        ML pipeline.
      </footer>
    </div>
  )
}

export default App
