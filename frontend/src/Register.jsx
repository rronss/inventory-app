import { useEffect, useState } from 'react'

import { api, setToken } from './api.js'
import BotCheck from './BotCheck.jsx'
import { usernameRule } from './username.js'

export default function Register({ onSignedIn }) {
  const [error, setError] = useState('')
  const [siteKey, setSiteKey] = useState('') // set when the server asks for a robot check
  const [token, setBotToken] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    api('/auth/config')
      .then((config) => setSiteKey(config.turnstile_site_key))
      .catch(() => {}) // the server still insists on the check if it wants one
  }, [])

  async function submit(event) {
    event.preventDefault()
    setError('')
    const { confirm, ...account } = Object.fromEntries(new FormData(event.target))
    if (confirm !== account.password) {
      setError('The two passwords are not the same')
      return
    }
    try {
      const body = { ...account, turnstile_token: token }
      delete body['cf-turnstile-response'] // the widget adds its own field to the form
      const { access_token } = await api('/auth/register', { method: 'POST', body })
      setToken(access_token)
      await onSignedIn()
    } catch (err) {
      setError(err.message)
      setBotToken('')
      setAttempt((n) => n + 1) // a token works once
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Register</h2>
      <label>
        Name
        <input name="name" autoComplete="name" maxLength="80" required />
      </label>
      <label>
        Username
        <input name="username" autoComplete="username" {...usernameRule} />
      </label>
      <label>
        Email
        <input name="email" type="email" autoComplete="email" required />
      </label>
      <label>
        Password (at least 8 characters)
        <input name="password" type="password" autoComplete="new-password" minLength="8" maxLength="72" required />
      </label>
      <label>
        Repeat the password
        <input name="confirm" type="password" autoComplete="new-password" required />
      </label>
      {siteKey && <BotCheck key={attempt} siteKey={siteKey} onToken={setBotToken} onProblem={setError} />}
      {error && <p className="error">{error}</p>}
      <button type="submit" className="wide">
        Create account
      </button>
      <p className="hint">
        Already registered? <a href="#/signin">Sign in</a>
      </p>
    </form>
  )
}
