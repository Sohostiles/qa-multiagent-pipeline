// Imports
import { useEffect, useState } from 'react'
import FindingsDashboard from './components/FindingsDashboard'
import RunSummary from './components/RunSummary'
import FindingDetail from './components/FindingDetail'
import RunList from './components/RunList'
import useRuns from './hooks/useRuns'
import ReportDownload from './components/ReportDownload'
import RunForm from './components/RunForm'
import './App.css'


function App() {
  // Saved runs and selected run
  const { runs, loading, error } = useRuns()
  const [selectedRun, setSelectedRun] = useState(null)

  // Findings for the selected run
  const [findings, setFindings] = useState([])
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [findingsError, setFindingsError] = useState('')
  const [selectedFinding, setSelectedFinding] = useState(null)

  // Load findings when another run is selected
  useEffect(() => {
    if (!selectedRun) return

    let ignore = false

    async function loadFindings() {
      setFindingsLoading(true)
      setFindingsError('')
      setFindings([])

      try {
        const response = await fetch(
          `/api/runs/${selectedRun.id}/findings`
        )

        if (!response.ok) {
          throw new Error('Could not load findings.')
        }

        const data = await response.json()

        if (!ignore) {
          setFindings(data)
        }
      } catch (err) {
        if (!ignore) {
          setFindingsError(err.message)
        }
      } finally {
        if (!ignore) {
          setFindingsLoading(false)
        }
      }
    }

    loadFindings()

    // Ignore old responses when the selected run changes
    return () => {
      ignore = true
    }
  }, [selectedRun])

  // Select a run and clear the previous findings
  function selectRun(run) {
    if (selectedRun?.id === run.id) return

    // Clear the open finding when switching runs
    setSelectedFinding(null)
    setFindings([])
    setFindingsError('')
    setFindingsLoading(true)
    setSelectedRun(run)
  }

  return (
    <main>
      <RunForm />
      <h1>QA Test Runs</h1>

      {selectedRun && (
        <section aria-labelledby="selected-run-heading">
          <h2 id="selected-run-heading">
            Run {selectedRun.id}
          </h2>

          <p>Target: {selectedRun.url}</p>
          <p>User: {selectedRun.username}</p>
          <p>Status: {selectedRun.status}</p>
          <ReportDownload
            key={selectedRun.id}
            runId={selectedRun.id}
          />

          {!findingsLoading && !findingsError && (
              <RunSummary findings={findings} />
            )}

          <h3>Findings</h3>

          <FindingsDashboard
            key={selectedRun.id}
            findings={findings}
            loading={findingsLoading}
            error={findingsError}
            onSelect={setSelectedFinding}
          />
          {selectedFinding && (
            <FindingDetail
              finding={selectedFinding}
              onClose={() => setSelectedFinding(null)}
            />
          )}
        </section>
      )}

      <RunList
        runs={runs}
        loading={loading}
        error={error}
        selectedRun={selectedRun}
        onSelect={selectRun}
      />
    </main>
  )
}

export default App