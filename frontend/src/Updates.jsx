import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'

const day = (date) => new Date(date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

// News for everyone: notes about the app, and messages from the admins.
export default function Updates({ user, onExpired, onRead }) {
  const [updates, setUpdates] = useState(null)
  const [writing, setWriting] = useState(false)
  const [removing, setRemoving] = useState(null) // id of the message asked about
  const [error, setError] = useState('')
  const isAdmin = user.role === 'admin'

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  // Opening the tab reads everything; what was new keeps its mark until the page is left.
  useEffect(() => {
    api('/updates')
      .then(async (found) => {
        setUpdates(found)
        await api('/updates/read', { method: 'POST' })
        onRead()
      })
      .catch(handle)
  }, [handle, onRead])

  async function post(event) {
    event.preventDefault()
    setError('')
    try {
      const entry = await api('/updates', { method: 'POST', body: Object.fromEntries(new FormData(event.target)) })
      setUpdates((shown) => [{ ...entry, unread: false }, ...shown])
      setWriting(false)
      await api('/updates/read', { method: 'POST' })
      onRead()
    } catch (err) {
      handle(err)
    }
  }

  async function remove(id) {
    setRemoving(null)
    try {
      await api(`/updates/${id}`, { method: 'DELETE' })
      setUpdates((shown) => shown.filter((entry) => entry.id !== id))
    } catch (err) {
      handle(err)
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>Updates</h1>
        {isAdmin && (
          <button type="button" className="tool primary" aria-expanded={writing} onClick={() => setWriting(!writing)}>
            New
          </button>
        )}
      </div>

      {writing && (
        <form className="card new-chat" onSubmit={post}>
          <label>
            Title
            <input name="title" maxLength="120" required autoFocus />
          </label>
          <label>
            Message to everyone
            <textarea name="text" rows="3" maxLength="1000" required />
          </label>
          <div className="dialog-actions">
            <button type="button" className="tool" onClick={() => setWriting(false)}>
              Cancel
            </button>
            <button type="submit" className="tool primary">
              Post
            </button>
          </div>
        </form>
      )}

      {error && <p className="error">{error}</p>}
      {updates === null && !error && <p className="hint">Loading…</p>}
      {updates?.length === 0 && <p className="card hint">No updates yet.</p>}

      {updates?.map((entry) => (
        <article key={entry.id} className={entry.unread ? 'card update unread' : 'card update'}>
          <p className="update-meta">
            <span className={`tag ${entry.kind}`}>{entry.kind === 'system' ? 'System' : 'Admin'}</span>
            {entry.unread && <span className="nav-count">New</span>}
            <small>
              {entry.author ? `${entry.author} · ` : ''}
              {day(entry.created_at)}
            </small>
          </p>
          <h2>{entry.title}</h2>
          <p className="description">{entry.text}</p>
          {isAdmin && entry.kind === 'admin' && (
            <p className="friend-actions">
              {removing === entry.id ? (
                <>
                  <span>Remove this message for everyone?</span>
                  <button type="button" className="tool solid-danger small" onClick={() => remove(entry.id)}>
                    Yes, remove
                  </button>
                  <button type="button" className="tool small" onClick={() => setRemoving(null)}>
                    Cancel
                  </button>
                </>
              ) : (
                <button type="button" className="tool danger small" onClick={() => setRemoving(entry.id)}>
                  Remove
                </button>
              )}
            </p>
          )}
        </article>
      ))}
    </>
  )
}
