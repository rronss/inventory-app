import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import { usernameRule } from './username.js'

export default function Users({ onExpired }) {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])
  const refresh = useCallback(() => api('/users').then(setUsers).catch(handle), [handle])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function addUser(event) {
    event.preventDefault()
    const form = event.target
    setError('')
    try {
      await api('/users', { method: 'POST', body: Object.fromEntries(new FormData(form)) })
      form.reset()
      await refresh()
    } catch (err) {
      handle(err)
    }
  }

  return (
    <>
      <h1>Users</h1>
      {error && <p className="error">{error}</p>}
      <section className="card">
        <ul className="list">
          {users.map((u) => (
            <li key={u.id}>
              <span>
                {u.username} {u.name && <small>{u.name}</small>}
              </span>
              <span>{u.role}</span>
            </li>
          ))}
        </ul>
      </section>
      <form className="card narrow" onSubmit={addUser}>
        <h2>Add a staff account</h2>
        <input name="name" placeholder="Name" maxLength="80" />
        <input name="username" placeholder="Username" autoComplete="off" {...usernameRule} />
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" autoComplete="new-password" placeholder="Password (8+)" minLength="8" required />
        <button type="submit">Create account</button>
      </form>
    </>
  )
}
