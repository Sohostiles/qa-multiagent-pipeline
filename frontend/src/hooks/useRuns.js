import { useEffect, useState } from 'react'

// Load saved runs when we open History or Projects
function useRuns(pathname) {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (pathname !== '/history' && pathname !== '/projects') return

    let ignore = false

    async function loadRuns() {
      setLoading(true)
      setError('')

      try {
        const response = await fetch('/api/runs')

        if (!response.ok) {
          throw new Error('Could not load test runs.')
        }

        const data = await response.json()

        if (!ignore) {
          setRuns(data)
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

    loadRuns()

    // Ignore old responses after leaving the page
    return () => {
      ignore = true
    }
  }, [pathname])

  return { runs, loading, error }
}

export default useRuns