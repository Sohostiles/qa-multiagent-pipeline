// Show saved runs and let the user select one
function RunList({ runs, loading, error, selectedRun, onSelect }) {
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
    <ul>
      {runs.map((run) => (
        <li key={run.id}>
          <button
            type="button"
            onClick={() => onSelect(run)}
            aria-pressed={selectedRun?.id === run.id}
          >
            View run {run.id}
          </button>

          <p>{run.url}</p>
          <p>{run.username} | {run.status}</p>
        </li>
      ))}
    </ul>
  )
}

export default RunList