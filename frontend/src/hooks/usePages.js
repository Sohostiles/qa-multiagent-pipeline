import { useEffect, useState } from 'react'

// Load the captured pages for a run
function usePages(runId) {
  const [pages, setPages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function loadPages() {
      setLoading(true)
      setError('')
      setPages([])

      try {
        const response = await fetch(`/api/runs/${runId}/pages`)

        if (!response.ok) {
          throw new Error('Could not load captured pages.')
        }

        const data = await response.json()

        if (!ignore) {
          setPages(data)
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

    loadPages()

    // Ignore old responses if the run changes
    return () => {
      ignore = true
    }
  }, [runId])

  return { pages, loading, error }
}

export default usePages