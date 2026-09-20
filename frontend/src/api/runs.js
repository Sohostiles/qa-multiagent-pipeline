// Send a new test request to the backend
export async function createRun(details) {
  const response = await fetch('/api/runs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(details),
  })

  if (!response.ok) {
    const message = response.status === 422
      ? 'Check the target URL and required login fields.'
      : 'Could not start the test.'

    throw new Error(message)
  }

  return response.json()
}