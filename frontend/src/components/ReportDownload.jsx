import { useState } from 'react'

// Download the saved report for a run
function ReportDownload({ runId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function downloadReport() {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/runs/${runId}/report`)

      if (!response.ok) {
        throw new Error(
          response.status === 404
            ? 'No report available for this run.'
            : 'Could not download the report.'
        )
      }

      // Prepare the response as a downloadable file
      const file = await response.blob()
      const url = URL.createObjectURL(file)
      const link = document.createElement('a')

      link.href = url
      link.download = `report_${runId}.md`
      document.body.appendChild(link)
      link.click()
      link.remove()

      // Release the temporary URL after the download starts
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={downloadReport}
        disabled={loading}
      >
        {loading ? 'Downloading...' : 'Download report'}
      </button>

      {error && <p role="alert">{error}</p>}
    </div>
  )
}

export default ReportDownload