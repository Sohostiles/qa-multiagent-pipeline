// Imports
import { useEffect, useState } from 'react'
import {
  NavLink,
  Route,
  Routes,
  useNavigate,
  useMatch,
  useLocation,
} from 'react-router'
import FindingsDashboard from './components/FindingsDashboard'
import FindingDetail from './components/FindingDetail'
import RunList from './components/RunList'
import useRuns from './hooks/useRuns'
import ReportDownload from './components/ReportDownload'
import RunForm from './components/RunForm'
import './App.css'

// Pages from the same website belong to one project
function getProjectUrl(url) {
  try {
    return new URL(url).origin
  } catch {
    // Keep older URLs visible even if they aren't valid
    return url
  }
}

const finishedStatuses = ['completed', 'failed', 'login_failed']

function App() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const runMatch = useMatch('/runs/:runId')
  const runId = runMatch?.params.runId

  // Saved runs
  const { runs, loading, error } = useRuns(pathname)

  // The run currently open
  const [selectedRun, setSelectedRun] = useState(null)
  const [runLoading, setRunLoading] = useState(false)
  const [runError, setRunError] = useState('')

  // Findings for that run
  const [findings, setFindings] = useState([])
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [findingsError, setFindingsError] = useState('')

  // Load the run and keep checking while it is running
  useEffect(() => {
    let ignore = false
    let timer

    setSelectedRun(null)
    setFindings([])
    setFindingsError('')
    setRunError('')
    setRunLoading(Boolean(runId))
    setFindingsLoading(Boolean(runId))

    if (!runId) return

    async function loadRun() {
      try {
        const response = await fetch(`/api/runs/${runId}`)

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? 'This run was not found.'
              : 'Could not load this run.'
          )
        }

        const data = await response.json()

        if (ignore) return

        setSelectedRun(data)
        setRunLoading(false)

        // Wait three seconds before checking again
        if (!finishedStatuses.includes(data.status)) {
          timer = setTimeout(loadRun, 3000)
        }
      } catch (err) {
        if (!ignore) {
          setRunError(err.message)
          setRunLoading(false)
        }
      }
    }

    loadRun()

    // Stop checking when we leave this run
    return () => {
      ignore = true
      clearTimeout(timer)
    }
  }, [runId])

  // Load findings once the assessment is complete
  useEffect(() => {
    if (
      !selectedRun ||
      String(selectedRun.id) !== runId ||
      selectedRun.status !== 'completed'
    ) {
      return
    }

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

    // Ignore the response if we switch to another run
    return () => {
      ignore = true
    }
  }, [selectedRun, runId])

  // Group saved runs by website
  const projects = new Map()

  for (const run of runs) {
    const projectUrl = getProjectUrl(run.url)

    if (!projects.has(projectUrl)) {
      projects.set(projectUrl, [])
    }

    projects.get(projectUrl).push(run)
  }

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <NavLink to="/" className="app-brand" end>
            QA<span>AutoPilot</span>
          </NavLink>

          <nav className="app-nav" aria-label="Main navigation">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/projects">
              Projects
            </NavLink>
            <NavLink to="/history">
              History
            </NavLink>
          </nav>
        </div>
      </header>

      <Routes>
        {/* Start a new test */}
        <Route
          path="/"
          element={
            <main>
              <h1>Dashboard</h1>
              <RunForm />
            </main>
          }
        />

        {/* All saved runs */}
        <Route
          path="/history"
          element={
            <main>
              <h1>Run history</h1>

              <RunList
                runs={runs}
                loading={loading}
                error={error}
              />
            </main>
          }
        />

        {/* Runs grouped by website */}
        <Route
          path="/projects"
          element={
            <main>
              <h1>Projects</h1>

              {loading && <p>Loading projects...</p>}
              {error && <p role="alert">{error}</p>}

              {!loading && !error && (
                projects.size === 0 ? (
                  <p>
                    No projects yet. Start a test from the dashboard.
                  </p>
                ) : (
                  Array.from(projects, ([projectUrl, projectRuns]) => (
                    <details key={projectUrl} className="project-group">
                      <summary>
                        {projectUrl} ({projectRuns.length}{' '}
                        {projectRuns.length === 1 ? 'run' : 'runs'})
                      </summary>

                      <RunList
                        runs={projectRuns}
                        loading={false}
                        error=""
                      />
                    </details>
                  ))
                )
              )}
            </main>
          }
        />

        {/* Progress and results for one run */}
        <Route
          path="/runs/:runId"
          element={
            <main>
              <NavLink to="/history" className="back-link">Back to history</NavLink>

              {runLoading && <p>Loading run...</p>}
              {runError && <p role="alert">{runError}</p>}

              {!runLoading &&
                !runError &&
                selectedRun &&
                String(selectedRun.id) === runId && (
                  <section aria-labelledby="selected-run-heading">
                    <header className="run-header">
                      <div className="run-header-title">
                        <h1 id="selected-run-heading">
                          Run #{selectedRun.id}
                        </h1>

                        <span className={`run-status run-status--${selectedRun.status}`}>
                          {selectedRun.status.replaceAll('_', ' ')}
                        </span>
                      </div>

                      <dl className="run-header-details">
                        <div>
                          <dt>Target URL</dt>
                          <dd>{selectedRun.url}</dd>
                        </div>

                        <div>
                          <dt>Test user</dt>
                          <dd>{selectedRun.username || 'Not provided'}</dd>
                        </div>
                      </dl>
                    </header>

                    {!finishedStatuses.includes(selectedRun.status) && (
                      <div role="status">
                        <h2>Assessment in progress</h2>
                        <p>
                          Results will appear here automatically when
                          the run is complete.
                        </p>
                        <p>
                          You can leave this page and return through
                          History.
                        </p>
                      </div>
                    )}

                    {selectedRun.status === 'login_failed' && (
                      <p role="alert">
                        Login failed. Check the test credentials and
                        login settings before starting another run.
                      </p>
                    )}

                    {selectedRun.status === 'failed' && (
                      <p role="alert">
                        The assessment could not finish. Check the
                        backend terminal for the error.
                      </p>
                    )}

                    {selectedRun.status === 'completed' && (
                      <>
                        <ReportDownload
                          key={selectedRun.id}
                          runId={selectedRun.id}
                        />

                        <FindingsDashboard
                            key={selectedRun.id}
                            runId={selectedRun.id}
                            findings={findings}
                            loading={findingsLoading}
                            error={findingsError}
                            onSelect={(finding) => navigate(`/findings/${finding.id}`)}
                        />
                      </>
                    )}
                  </section>
                )}
            </main>
          }
        />

        {/* A finding opens on its own page */}
        <Route
          path="/findings/:findingId"
          element={<FindingDetail />}
        />

        <Route
          path="*"
          element={
            <main>
              <h1>Page not found</h1>
              <NavLink to="/">Back to dashboard</NavLink>
            </main>
          }
        />
      </Routes>
    </>
  )
}

export default App