import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { personLink } from './itemControls.jsx'
import { usernameRule } from './username.js'

// Who has an account. Click one to open their record.
function Users({ handle }) {
  const [users, setUsers] = useState(null)

  useEffect(() => {
    api('/users').then(setUsers).catch(handle)
  }, [handle])

  return (
    <section className="card panel">
      <h3>
        Users <span className="tag">{users?.length ?? 0}</span>
      </h3>
      <ul className="rows">
        {users?.map((u) => (
          <li key={u.id}>
            <a className="row" href={personLink(u.id)}>
              <Avatar user={u} small />
              <span>
                {u.username} {u.name && <small>{u.name}</small>}
              </span>
              <span>
                {u.role} <span aria-hidden="true">›</span>
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}

function Staff({ handle, clear }) {
  const [created, setCreated] = useState(null)

  async function addAccount(event) {
    event.preventDefault()
    const form = event.target
    clear()
    setCreated(null)
    try {
      setCreated(await api('/users', { method: 'POST', body: Object.fromEntries(new FormData(form)) }))
      form.reset()
    } catch (err) {
      handle(err)
    }
  }

  return (
    <>
      {created && (
        <p className="ok">
          Account created for <a href={personLink(created.id)}>{created.username}</a>.
        </p>
      )}
      <form className="card narrow" onSubmit={addAccount}>
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

export default function Admin({ tab, onExpired }) {
  const [error, setError] = useState('')
  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])
  const clear = useCallback(() => setError(''), [])

  return (
    <>
      <h1>Admin</h1>
      {error && <p className="error">{error}</p>}
      {tab === 'staff' ? <Staff handle={handle} clear={clear} /> : <Users handle={handle} />}
    </>
  )
}
