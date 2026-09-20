// Show one finding and a button to open its details
function FindingCard({ finding, onSelect }) {
  return (
    <li className="finding-card">
      <p>{finding.description}</p>
      <p className="finding-page">{finding.page_url}</p>

      <button
        type="button"
        onClick={() => onSelect(finding)}
      >
        View finding {finding.id}
      </button>
    </li>
  )
}

export default FindingCard