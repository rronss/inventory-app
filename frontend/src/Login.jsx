import { useState } from 'react'

import { api, setToken } from './api.js'

export default function Login({ onSignedIn }) {
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    const form = new FormData(event.target)
    try {
      const { access_token } = await api('/auth/login', {
        method: 'POST',
        body: { login: form.get('login'), password: form.get('password') },
      })
      setToken(access_token)
      await onSignedIn()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Sign in</h2>
      <label>
        Email or username
        <input name="login" autoComplete="username" required />
      </label>
      <label>
        Password
        <input name="password" type="password" autoComplete="current-password" required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" className="wide">
        Sign in
      </button>
      <p className="hint">
        No account yet? <a href="#/register">Register</a>
      </p>
    </form>
  )
}
