import usePages from '../hooks/usePages'
import ScreenshotPreview from './ScreenshotPreview'

// Show captures of the page linked to this finding
function FindingScreenshots({ finding }) {
  const { pages, loading, error } = usePages(finding.run_id)

  if (loading) {
    return <p>Loading screenshots...</p>
  }

  if (error) {
    return <p role="alert">{error}</p>
  }

  // A URL can have several captured states
  const matchingPages = pages.filter(
    (page) => page.url === finding.page_url
  )

  if (matchingPages.length === 0) {
    return <p>No captured pages available for this finding.</p>
  }

  return (
    <section aria-label="Page screenshots">
      <h3>Page screenshots</h3>
      <p>
        Captures of the affected URL. The finding does not identify
        which capture contains the issue.
      </p>

      {matchingPages.map((page) => (
        <figure key={page.id}>
          <figcaption>
            Capture {page.id}
            {page.step !== null && ` | Step ${page.step}`}
            {page.action && ` | ${page.action}`}
          </figcaption>

          {page.screenshot_path ? (
            <ScreenshotPreview key={page.id} page={page} />
          ) : (
            <p>No screenshot saved.</p>
          )}
        </figure>
      ))}
    </section>
  )
}

export default FindingScreenshots