import FindingScreenshots from './FindingScreenshots'

// Show the details of the selected finding
function FindingDetail({ finding, onClose }) {
  return (
    <section aria-labelledby="finding-detail-heading">
      <h2 id="finding-detail-heading">
        Finding {finding.id}
      </h2>

      <button type="button" onClick={onClose}>
        Close details
      </button>

      <p>Severity: {finding.severity}</p>
      <p>Type: {finding.issue_type}</p>
      <p>Page: {finding.page_url}</p>

      <h3>Description</h3>
      <p>{finding.description}</p>

      <h3>Location</h3>
      <p>{finding.location || 'Not specified'}</p>

      <h3>Suggested fix</h3>
      <p>{finding.recommended_fix || 'No suggested fix available.'}</p>

      <h3>Analysis source</h3>
      <p>{finding.source || 'Not specified'}</p>

      <p>Agent confidence: {finding.confidence || 'Not specified'}</p>

      <FindingScreenshots
         key={finding.run_id}
         finding={finding}
      />
    </section>
  )
}

export default FindingDetail