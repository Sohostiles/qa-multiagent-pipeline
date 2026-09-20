import { useEffect, useState } from 'react'

// Load the saved test runs
function useRuns() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function loadRuns() {
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

    // Ignore the response if the component has been removed
    return () => {
      ignore = true
    }
  }, [])

  return { runs, loading, error }
}

export default useRuns