import { useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import EditProfile from './EditProfile.jsx'
import Person from './Person.jsx'
import ProfileMenu from './ProfileMenu.jsx'
import SecuritySettings from './SecuritySettings.jsx'

// "Profile" is your record; "Settings" is where you change it.
export default function Profile({ page, tab, user, onChanged, onExpired }) {
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
        <h1>{page === 'settings' ? 'Settings' : 'Profile'}</h1>
        {page !== 'settings' && <ProfileMenu own />}
      </div>

      {page !== 'settings' ? (
        <Person id={user.id} user={user} onExpired={onExpired} inProfile />
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
