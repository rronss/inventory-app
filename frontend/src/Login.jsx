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
        body: { email: form.get('email'), password: form.get('password') },
      })
      setToken(access_token)
      await onSignedIn()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="card center" onSubmit={submit}>
      <h1>Sign in</h1>
      <label>
        Email
        <input name="email" type="email" autoComplete="username" required />
      </label>
      <label>
        Password
        <input name="password" type="password" autoComplete="current-password" required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Sign in</button>
      <p className="hint">Accounts are created by an admin.</p>
    </form>
  )
}
