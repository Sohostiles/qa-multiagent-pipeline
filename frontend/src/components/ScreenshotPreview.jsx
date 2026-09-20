import { useState } from 'react'

// Show a screenshot and handle missing image files
function ScreenshotPreview({ page }) {
  const [error, setError] = useState(false)
  const screenshotUrl = `/api/pages/${page.id}/screenshot`

  if (error) {
    return <p>Screenshot could not be loaded.</p>
  }

  return (
    <a
      href={screenshotUrl}
      target="_blank"
      rel="noreferrer"
    >
      <img
        src={screenshotUrl}
        alt={`Capture ${page.id} of ${page.url}`}
        loading="lazy"
        onError={() => setError(true)}
        style={{
          display: 'block',
          maxWidth: '100%',
          maxHeight: '400px',
          objectFit: 'contain',
        }}
      />
      Open full screenshot
    </a>
  )
}

export default ScreenshotPreview