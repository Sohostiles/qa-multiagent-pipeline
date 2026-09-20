import { useState } from 'react'
import { createRun } from '../api/runs'

// Collect the target and optional login details
function RunForm() {
  const [url, setUrl] = useState('')
  const [useLogin, setUseLogin] = useState(false)

  const [login, setLogin] = useState({
    url: '',
    username: '',
    password: '',
    username_selector: '',
    password_selector: '',
    submit_selector: '',
    success_url: '',
  })
  
  // Track the request to start a test
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [createdRun, setCreatedRun] = useState(null)

  // Update one login field and keep the other values
  function updateLogin(event) {
    const { name, value } = event.target

    setLogin((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  // Prepare the form data and request a new run
async function startRun(event) {
  event.preventDefault()

  if (submitting) return

  setSubmitting(true)
  setError('')
  setCreatedRun(null)

  try {
    const details = {
      url: url.trim(),
    }

    if (useLogin) {
      details.login = {
        ...login,
        url: login.url.trim(),
        username_selector: login.username_selector.trim(),
        password_selector: login.password_selector.trim(),
        submit_selector: login.submit_selector.trim(),
        success_url: login.success_url.trim() || null,
      }
    }

    const result = await createRun(details)
    setCreatedRun(result.run_id)

    // Clear the password after the request is accepted
    setLogin((previous) => ({
      ...previous,
      password: '',
    }))
  } catch (err) {
    setError(err.message)
  } finally {
    setSubmitting(false)
  }
}

  return (
    <section aria-labelledby="new-run-heading">
      <h2 id="new-run-heading">New test run</h2>

      <form onSubmit={startRun}>
        <div>
          <label htmlFor="target-url">Target URL</label>
          <input
            id="target-url"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.com"
            required
          />
        </div>

        <label>
          <input
            type="checkbox"
            checked={useLogin}
            onChange={(event) => setUseLogin(event.target.checked)}
          />
          Log in before testing
        </label>

        {useLogin && (
          <fieldset>
            <legend>Test user login</legend>

            <div>
              <label htmlFor="login-url">Login page URL</label>
              <input
                id="login-url"
                name="url"
                type="url"
                value={login.url}
                onChange={updateLogin}
                required
              />
            </div>

            <div>
              <label htmlFor="login-username">Username</label>
              <input
                id="login-username"
                name="username"
                type="text"
                value={login.username}
                onChange={updateLogin}
                autoComplete="off"
                required
              />
            </div>

            <div>
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                name="password"
                type="password"
                value={login.password}
                onChange={updateLogin}
                autoComplete="off"
                required
              />
            </div>

            <fieldset>
              <legend>Advanced login settings</legend>
              <p>
                Enter the selectors for the login fields and submit button.
              </p>

              <div>
                <label htmlFor="username-selector">
                  Username field selector
                </label>
                <input
                  id="username-selector"
                  name="username_selector"
                  type="text"
                  value={login.username_selector}
                  onChange={updateLogin}
                  placeholder="#username"
                  required
                />
              </div>

              <div>
                <label htmlFor="password-selector">
                  Password field selector
                </label>
                <input
                  id="password-selector"
                  name="password_selector"
                  type="text"
                  value={login.password_selector}
                  onChange={updateLogin}
                  placeholder="#password"
                  required
                />
              </div>

              <div>
                <label htmlFor="submit-selector">
                  Submit button selector
                </label>
                <input
                  id="submit-selector"
                  name="submit_selector"
                  type="text"
                  value={login.submit_selector}
                  onChange={updateLogin}
                  placeholder="button[type='submit']"
                  required
                />
              </div>

              <div>
                <label htmlFor="success-url">
                  Expected URL after login (optional)
                </label>
                <input
                  id="success-url"
                  name="success_url"
                  type="url"
                  value={login.success_url}
                  onChange={updateLogin}
                />
              </div>
            </fieldset>
          </fieldset>
        )}

        <button type="submit" disabled={submitting}>
            {submitting ? 'Starting...' : 'Run test'}
        </button>

        {error && <p role="alert">{error}</p>}

        {createdRun !== null && (
        <p role="status">
            Run {createdRun} accepted. The assessment will run in the background.
        </p>
        )}
        
      </form>
    </section>
  )
}

export default RunForm