import { Link } from 'react-router'

// Show saved runs with links to their results
function RunList({ runs, loading, error }) {
  if (loading) {
    return <p>Loading test runs...</p>
  }

  if (error) {
    return <p role="alert">{error}</p>
  }

  if (runs.length === 0) {
    return <p>No test runs yet.</p>
  }

  return (
    <ul className="run-list">
      {runs.map((run) => (
        <li key={run.id} className="run-list-item">
          <div className="run-list-info">
            <Link className="run-list-title" to={`/runs/${run.id}`}>
              Run #{run.id}
            </Link>

            <p className="run-list-url">{run.url}</p>
            <p className="run-list-user">
              Test user: {run.username || 'Not provided'}
            </p>
          </div>

          <span className={`run-status run-status--${run.status}`}>
            {run.status.replaceAll('_', ' ')}
          </span>
        </li>
      ))}
    </ul>
  )
}

export default RunList