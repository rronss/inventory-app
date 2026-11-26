import { useState } from 'react'

import { api, setToken } from './api.js'
import { usernameRule } from './username.js'

export default function Register({ onSignedIn }) {
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    const { confirm, ...account } = Object.fromEntries(new FormData(event.target))
    if (confirm !== account.password) {
      setError('The two passwords are not the same')
      return
    }
    try {
      const { access_token } = await api('/auth/register', { method: 'POST', body: account })
      setToken(access_token)
      await onSignedIn()
    } catch (err) {
      setError(err.message)
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
