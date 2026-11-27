import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import { FriendButton, useFriends } from './Friends.jsx'
import { itemLink, personLink } from './itemControls.jsx'

const KINDS = {
  low_stock: ['Low stock', 'warn'],
  out_of_stock: ['Out of stock', 'warn'],
  stock_changed: ['Stock changed', ''],
  item_edited: ['Item edited', ''],
  item_removed: ['Item removed', 'warn'],
  permissions_changed: ['Permissions', 'account'],
  friend_request: ['Friend request', 'account'],
  friend_accepted: ['Friend', 'account'],
}
const PAGE = 50

// Where an alert leads. A removed item has no page to open.
function target(alert) {
  if (alert.kind === 'permissions_changed') return '#/profile'
  if (alert.person_id) return personLink(alert.person_id)
  return alert.item_id ? itemLink({ id: alert.item_id }) : null
}

export default function Alerts({ onExpired, onRead }) {
  const [alerts, setAlerts] = useState(null)
  const [more, setMore] = useState(false)
  const [error, setError] = useState('')
  const friends = useFriends(onExpired)

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  const load = useCallback(
    async (before) => {
      try {
        const page = await api(`/inbox?limit=${PAGE}${before ? `&before=${before}` : ''}`)
        setAlerts((shown) => (before ? [...shown, ...page] : page))
        setMore(page.length === PAGE)
      } catch (err) {
        handle(err)
      }
    },
    [handle],
  )

  useEffect(() => {
    load()
  }, [load])

  async function open(alert) {
    try {
      if (!alert.is_read) {
        await api(`/inbox/${alert.id}/read`, { method: 'POST' })
        setAlerts((shown) => shown.map((other) => (other.id === alert.id ? { ...other, is_read: true } : other)))
        onRead()
      }
      if (target(alert)) window.location.hash = target(alert)
    } catch (err) {
      handle(err)
    }
  }

  async function readAll() {
    try {
      await api('/inbox/read', { method: 'POST' })
      setAlerts((shown) => shown.map((alert) => ({ ...alert, is_read: true })))
      onRead()
    } catch (err) {
      handle(err)
    }
  }

  const unread = alerts?.filter((alert) => !alert.is_read).length ?? 0

  // Answering a request here also marks it as dealt with.
  async function answer(alert, action) {
    await friends.act(alert.person_id, action)
    await load()
    onRead()
  }

  return (
    <>
      <div className="page-head">
        <h1>Alerts</h1>
        {unread > 0 && (
          <button type="button" className="tool" onClick={readAll}>
            Mark all as read
          </button>
        )}
      </div>
      {error && <p className="error">{error}</p>}
      <section className="card">
        {alerts === null && !error && <p className="hint">Loading…</p>}
        {alerts?.length === 0 && (
          <p className="hint">Nothing yet. Alerts about items you added, and about your account, arrive here.</p>
        )}
        <ul className="alerts">
          {alerts?.map((alert) => {
            const [label, tone] = KINDS[alert.kind] || [alert.kind, '']
            return (
              <li key={alert.id}>
                <button type="button" className={alert.is_read ? 'alert' : 'alert unread'} onClick={() => open(alert)}>
                  <span className={`dot ${tone}`} aria-hidden="true" />
                  <span className="alert-body">
                    <small>
                      {label}
                      {!alert.is_read && ' · New'}
                    </small>
                    <span>{alert.text}</span>
                  </span>
                  <small>{new Date(alert.created_at).toLocaleString()}</small>
                </button>
                {alert.kind === 'friend_request' && friends.statusOf(alert.person_id) === 'received' && (
                  <div className="alert-answer">
                    <FriendButton status="received" onAct={(action) => answer(alert, action)} small />
                  </div>
                )}
              </li>
            )
          })}
        </ul>
        {more && (
          <p>
            <button type="button" className="secondary" onClick={() => load(alerts[alerts.length - 1].id)}>
              Show older
            </button>
          </p>
        )}
      </section>
    </>
  )
}
