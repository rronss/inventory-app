import { useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import EditProfile from './EditProfile.jsx'
import Person from './Person.jsx'
import SecuritySettings from './SecuritySettings.jsx'

export default function Profile({ tab, user, onChanged, onSignOut, onExpired }) {
  const [message, setMessage] = useState(null)

  const clear = () => setMessage(null)
  const fail = (text) => setMessage({ ok: false, text })

  // Saves one form. Returns true when the server accepted it.
  async function save(form, path, method, body, done) {
    setMessage(null)
    try {
      await api(path, { method, body })
      setMessage({ ok: true, text: done })
      if (method === 'POST') form.reset()
      else await onChanged() // the account shown on this page changed
      return true
    } catch (err) {
      if (err.status === 401) onExpired()
      else setMessage({ ok: false, text: err.message })
      return false
    }
  }

  const notice = message && <p className={message.ok ? 'ok' : 'error'}>{message.text}</p>

  return (
    <>
      <div className="page-head">
        <h1>Profile</h1>
        <button type="button" className="tool" onClick={onSignOut}>
          Sign out
        </button>
      </div>

      {tab !== 'edit' && tab !== 'security' ? (
        <Person id={user.id} user={user} onExpired={onExpired} />
      ) : (
        <>
          <div className="who">
            <Avatar user={user} />
            <div>
              <strong>{user.username}</strong> <span className="hint">· {user.role}</span>
              {user.bio && <p className="description">{user.bio}</p>}
            </div>
          </div>

          {tab === 'security' ? (
            <SecuritySettings user={user} save={save} notice={notice} onSwitch={clear} />
          ) : (
            <EditProfile user={user} save={save} notice={notice} fail={fail} onSwitch={clear} />
          )}
        </>
      )}
    </>
  )
}
