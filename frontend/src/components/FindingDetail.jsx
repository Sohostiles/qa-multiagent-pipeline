import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import usePages from '../hooks/usePages'

// Open the full screenshot when clicked
function ScreenshotPreview({ page }) {
  const [error, setError] = useState(false)
  const screenshotUrl = `/api/pages/${page.id}/screenshot`

  if (error) {
    return <p>Could not load this screenshot.</p>
  }

  return (
    <a
      className="screenshot-link"
      href={screenshotUrl}
      target="_blank"
      rel="noreferrer"
    >
      <img
        src={screenshotUrl}
        alt={`Capture ${page.id} of ${page.url}`}
        loading="lazy"
        onError={() => setError(true)}
      />
      <span>Open full screenshot</span>
    </a>
  )
}

// Show captures from the affected page
function FindingScreenshots({ finding }) {
  const { pages, loading, error } = usePages(finding.run_id)

  if (loading) {
    return <p>Loading screenshots...</p>
  }

  if (error) {
    return <p role="alert">{error}</p>
  }

  const matchingPages = pages.filter(
    (page) => page.url === finding.page_url
  )

  if (matchingPages.length === 0) {
    return <p>No captured pages found for this finding.</p>
  }

  return (
    <>
      <p className="screenshot-note">
        Captures from the affected page. They may show different
        steps, so not every screenshot will show the issue.
      </p>

      {matchingPages.map((page) => (
        <figure className="finding-capture" key={page.id}>
          <figcaption>
            Capture {page.id}
            {page.step != null && ` | Step ${page.step}`}
            {page.action && ` | ${page.action}`}
          </figcaption>

          {page.screenshot_path ? (
            <ScreenshotPreview page={page} />
          ) : (
            <p>No screenshot saved.</p>
          )}
        </figure>
      ))}
    </>
  )
}

// Load the finding from its URL
function FindingDetail() {
  const { findingId } = useParams()
  const [finding, setFinding] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    setLoading(true)
    setError('')
    setFinding(null)

    async function loadFinding() {
      try {
        const response = await fetch(`/api/findings/${findingId}`)

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? 'This finding was not found.'
              : 'Could not load this finding.'
          )
        }

        const data = await response.json()

        if (!ignore) {
          setFinding(data)
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

    loadFinding()

    // Ignore the response if we leave this finding
    return () => {
      ignore = true
    }
  }, [findingId])

  if (loading) {
    return <main><p>Loading finding...</p></main>
  }

  if (error) {
    return (
      <main>
        <Link to="/history">Back to history</Link>
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!finding || String(finding.id) !== findingId) {
    return <main><p>Loading finding...</p></main>
  }

  return (
    <main className="finding-detail">
      <Link to={`/runs/${finding.run_id}`}>
        Back to run {finding.run_id}
      </Link>

      <header className="finding-detail-header">
        <div className="finding-detail-labels">
          <span className={`severity-label severity-label--${finding.severity}`}>
            {finding.severity}
          </span>
          <span>{finding.issue_type}</span>
        </div>

        <h1>Finding #{finding.id}</h1>
        <p className="finding-detail-url">{finding.page_url}</p>
      </header>

      <div className="finding-detail-grid">
        <section className="finding-detail-panel">
          <h2>Page screenshots</h2>

          <FindingScreenshots
            key={finding.run_id}
            finding={finding}
          />
        </section>

        <section className="finding-detail-panel">
          <h2>Description</h2>
          <p className="finding-detail-description">
            {finding.description}
          </p>

          <dl className="finding-metadata">
            <div>
              <dt>Location</dt>
              <dd>{finding.location || 'Not specified'}</dd>
            </div>

            <div>
              <dt>Analysis source</dt>
              <dd>{finding.source || 'Not specified'}</dd>
            </div>

            <div>
              <dt>Agent confidence</dt>
              <dd>{finding.confidence || 'Not specified'}</dd>
            </div>
          </dl>
        </section>
      </div>

      <section className="finding-detail-fix">
        <h2>Suggested fix</h2>
        <p>
          {finding.recommended_fix || 'No suggested fix available.'}
        </p>
      </section>
    </main>
  )
}

export default FindingDetail