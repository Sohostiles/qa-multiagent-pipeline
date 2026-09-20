import './RunSummary.css'

// Show the number of findings in each severity group
function RunSummary({ findings }) {
  const critical = findings.filter(
    (finding) => finding.severity === 'critical'
  ).length

  const major = findings.filter(
    (finding) => finding.severity === 'major'
  ).length

  const minor = findings.filter(
    (finding) => finding.severity === 'minor'
  ).length

  return (
    <dl className="run-summary">
      <div>
        <dt>Critical</dt>
        <dd>{critical}</dd>
      </div>

      <div>
        <dt>Major</dt>
        <dd>{major}</dd>
      </div>

      <div>
        <dt>Minor</dt>
        <dd>{minor}</dd>
      </div>

      <div>
        <dt>Total</dt>
        <dd>{findings.length}</dd>
      </div>
    </dl>
  )
}

export default RunSummary