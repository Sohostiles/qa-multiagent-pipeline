import { useState } from 'react'
import usePages from '../hooks/usePages'
import './FindingsDashboard.css'
import './RunSummary.css'

const severities = ['critical', 'major', 'minor']

// Count findings for the whole run
function RunSummary({ findings }) {
  return (
    <dl className="run-summary">
      {severities.map((severity) => (
        <div key={severity}>
          <dt>
            {severity.charAt(0).toUpperCase() + severity.slice(1)}
          </dt>
          <dd>
            {findings.filter(
              (finding) => finding.severity === severity
            ).length}
          </dd>
        </div>
      ))}

      <div>
        <dt>Total</dt>
        <dd>{findings.length}</dd>
      </div>
    </dl>
  )
}

// One finding and a screenshot of its page
function FindingCard({
  finding,
  page,
  pagesLoading,
  pagesError,
  onSelect,
}) {
  const [imageError, setImageError] = useState(false)

  return (
    <li className="finding-card">
      <div className="finding-preview">
        {pagesLoading ? (
          <p>Loading preview...</p>
        ) : pagesError ? (
          <p>Could not load page preview.</p>
        ) : page && !imageError ? (
          <figure>
            <img
              src={`/api/pages/${page.id}/screenshot`}
              alt={`Page capture of ${finding.page_url}`}
              loading="lazy"
              onError={() => setImageError(true)}
            />
            <figcaption>Page preview</figcaption>
          </figure>
        ) : (
          <p>No preview available.</p>
        )}
      </div>

      <div className="finding-card-content">
        <p className="finding-description">
          {finding.description}
        </p>

        <p className="finding-page">{finding.page_url}</p>

        {finding.recommended_fix && (
          <div className="finding-fix">
            <strong>Suggested fix</strong>
            <p>{finding.recommended_fix}</p>
          </div>
        )}

        <div className="finding-card-footer">
          <span>Finding #{finding.id}</span>

          <button type="button" onClick={() => onSelect(finding)}>
            View report
          </button>
        </div>
      </div>
    </li>
  )
}

function FindingsDashboard({
  runId,
  findings,
  loading,
  error,
  onSelect,
}) {
  const [selectedPage, setSelectedPage] = useState('')

  // Load the saved pages once for all cards
  const {
    pages,
    loading: pagesLoading,
    error: pagesError,
  } = usePages(runId)

  if (loading) {
    return <p>Loading findings...</p>
  }

  if (error) {
    return <p role="alert">{error}</p>
  }

  // Leave out anything classified as not a bug
  const reportFindings = findings.filter(
    (finding) => severities.includes(finding.severity)
  )

  // Each URL only needs to appear once in the dropdown
  const pageUrls = [
    ...new Set(reportFindings.map((finding) => finding.page_url)),
  ]

  const filteredFindings = selectedPage
    ? reportFindings.filter(
        (finding) => finding.page_url === selectedPage
      )
    : reportFindings

  return (
    <>
      {/* Keep the full run totals when filtering */}
      <RunSummary findings={reportFindings} />

      <h3>Findings</h3>

      {reportFindings.length === 0 ? (
        <p>No reportable findings saved for this run.</p>
      ) : (
        <>
          <label htmlFor="page-filter">Filter by page: </label>
          <select
            id="page-filter"
            value={selectedPage}
            onChange={(event) => setSelectedPage(event.target.value)}
          >
            <option value="">All pages</option>

            {pageUrls.map((url) => (
              <option key={url} value={url}>
                {url}
              </option>
            ))}
          </select>

          <div className="findings-dashboard">
            {severities.map((severity) => {
              const severityFindings = filteredFindings.filter(
                (finding) => finding.severity === severity
              )

              return (
                <section
                  key={severity}
                  className={`findings-column findings-column--${severity}`}
                >
                  <h4 className="findings-column-title">
                    {severity} ({severityFindings.length})
                  </h4>

                  {severityFindings.length === 0 ? (
                    <p>No findings in this group.</p>
                  ) : (
                    <ul className="findings-list">
                      {severityFindings.map((finding) => {
                        // Use the first screenshot of the affected URL
                        const page = pages.find(
                          (page) =>
                            page.url === finding.page_url &&
                            page.screenshot_path
                        )

                        return (
                          <FindingCard
                            key={`${finding.id}-${page?.id ?? 'none'}`}
                            finding={finding}
                            page={page}
                            pagesLoading={pagesLoading}
                            pagesError={pagesError}
                            onSelect={onSelect}
                          />
                        )
                      })}
                    </ul>
                  )}
                </section>
              )
            })}
          </div>
        </>
      )}
    </>
  )
}

export default FindingsDashboard