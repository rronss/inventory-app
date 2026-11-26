import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import { MoveStock, Owner } from './itemControls.jsx'

// The profile of one item.
export default function Item({ id, user, onExpired }) {
  const [item, setItem] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  const refresh = useCallback(async () => {
    try {
      const [found, movements] = await Promise.all([api(`/items/${id}`), api(`/items/${id}/movements`)])
      setItem(found)
      setHistory(movements)
    } catch (err) {
      handle(err)
    }
  }, [id, handle])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function send(path, options, form) {
    setError('')
    try {
      await api(path, { method: 'POST', ...options })
      form?.reset()
    } catch (err) {
      handle(err)
    }
    await refresh()
  }

  const path = (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <a href="#/inventory">Items</a>
      <span aria-hidden="true">&gt;</span>
      <span aria-current="page">ID {id}</span>
    </nav>
  )
  if (!item) {
    return (
      <>
        {path}
        {error ? <p className="error">{error}</p> : <p className="hint">Loading…</p>}
      </>
    )
  }

  return (
    <>
      {path}
      <h1>{item.name}</h1>
      <p className="hint">
        ID {item.id} · SKU {item.sku}
      </p>
      {error && <p className="error">{error}</p>}

      <section className={item.low_stock ? 'card low' : 'card'}>
        <h2>Stock</h2>
        <p>
          <strong>{item.quantity}</strong> in stock, reorder at {item.reorder_level}
          {item.low_stock && ' (low stock)'}
        </p>
        <MoveStock item={item} send={send} withNote />
      </section>

      <section className="card">
        <h2>Attached to</h2>
        <p>
          <Owner item={item} user={user} send={send} />
        </p>
      </section>

      <section className="card">
        <h2>History</h2>
        {history.length === 0 && <p className="hint">No stock movements yet.</p>}
        <ul className="list">
          {history.map((entry) => (
            <li key={entry.id}>
              <span>
                <strong>{entry.change > 0 ? `+${entry.change}` : entry.change}</strong> by {entry.username}
                {entry.note && <small>{entry.note}</small>}
              </span>
              <span className="hint">{new Date(entry.created_at).toLocaleString()}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
