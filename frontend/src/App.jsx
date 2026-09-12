import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function loadRuns() {
      try {
        const response = await fetch('/api/runs')

        if (!response.ok) {
          throw new Error('Could not load test runs.')
        }

        const data = await response.json()

        if (!ignore) {
          setRuns(data)
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message)
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    loadRuns()

    return () => {
      ignore = true
    }
  }, [])

  return (
    <main>
      <h1>QA Test Runs</h1>

      {loading && <p>Loading test runs...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && (
        runs.length === 0 ? (
          <p>No test runs yet.</p>
        ) : (
          <ul>
            {runs.map((run) => (
              <li key={run.id}>
                <strong>Run {run.id}</strong>
                <p>{run.url}</p>
                <p>{run.username} | {run.status}</p>
              </li>
            ))}
          </ul>
        )
      )}
    </main>
  )
}

export default App