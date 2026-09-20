import './FindingsDashboard.css'
import FindingCard from './FindingCard'
import { useState } from 'react'

// Display findings from highest to lowest severity
const severities = ['critical', 'major', 'minor']

function FindingsDashboard({ findings, loading, error, onSelect }) {
  // Filter findings by the affected page
  const [selectedPage, setSelectedPage] = useState('')

  if (loading) {
    return <p>Loading findings...</p>
  }

  if (error) {
    return <p role="alert">{error}</p>
  }

  if (findings.length === 0) {
    return <p>No saved findings for this run.</p>
  }

  // Get each page URL once for the dropdown
  const pages = [...new Set(findings.map((finding) => finding.page_url))]

  // Show all findings unless a page is selected
  const filteredFindings = selectedPage
    ? findings.filter((finding) => finding.page_url === selectedPage)
    : findings

  return (
    <>
    <label htmlFor="page-filter">Filter by page: </label>
    <select
      id="page-filter"
      value={selectedPage}
      onChange={(event) => setSelectedPage(event.target.value)}
    >
      <option value="">All pages</option>

      {pages.map((page) => (
        <option key={page} value={page}>
          {page}
        </option>
      ))}
    </select>
    
    <div className="findings-dashboard">
      {severities.map((severity) => {
        // Find the issues belonging to this severity
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
                {severityFindings.map((finding) => (
                  <FindingCard
                    key={finding.id}
                    finding={finding}
                    onSelect={onSelect}
                  />
                ))}
              </ul>
            )}
          </section>
        )
      })}
    </div>
    </>
  )
} 

export default FindingsDashboard