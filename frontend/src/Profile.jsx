import { useState } from 'react'

import { api } from './api.js'
import { usernameRule } from './username.js'

export default function Profile({ user, onChanged, onExpired }) {
  const [message, setMessage] = useState(null)

  async function submit(event, path, method, body, done) {
    event.preventDefault()
    const form = event.target
    setMessage(null)
    try {
      await api(path, { method, body })
      setMessage({ ok: true, text: done })
      if (method === 'PATCH') await onChanged()
      else form.reset()
    } catch (err) {
      if (err.status === 401) onExpired()
      else setMessage({ ok: false, text: err.message })
    }
  }

  const field = (event, name) => new FormData(event.target).get(name)

  return (
    <>
      <h1>My profile</h1>
      <p className="hint">
        {user.username} · {user.role}
      </p>
      {message && <p className={message.ok ? 'ok' : 'error'}>{message.text}</p>}

      <form
        key={`${user.name}|${user.username}`}
        className="card narrow"
        onSubmit={(e) =>
          submit(e, '/auth/me', 'PATCH', { name: field(e, 'name'), username: field(e, 'username') }, 'Profile saved')
        }
      >
        <h2>Name and username</h2>
        <input name="name" defaultValue={user.name} maxLength="80" placeholder="Name" aria-label="Name" />
        <input
          name="username"
          defaultValue={user.username}
          placeholder="Username"
          aria-label="Username"
          {...usernameRule}
        />
        <button type="submit">Save profile</button>
      </form>

      <form
        className="card narrow"
        onSubmit={(e) =>
          submit(
            e,
            '/auth/password',
            'POST',
            { current_password: field(e, 'current'), new_password: field(e, 'next') },
            'Password changed',
          )
        }
      >
        <h2>Password</h2>
        <input name="current" type="password" autoComplete="current-password" placeholder="Current password" required />
        <input name="next" type="password" autoComplete="new-password" placeholder="New password (8+)" minLength="8" required />
        <button type="submit">Change password</button>
      </form>
    </>
  )
}
