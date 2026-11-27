import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import Breadcrumb from './Breadcrumb.jsx'
import { may, MoveStock, personLink } from './itemControls.jsx'
import { Slideshow } from './itemImage.jsx'

function Details({ rows }) {
  return (
    <dl className="details-list">
      {rows.map(([term, value]) => (
        <div key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  )
}

// The profile of one item.
export default function Item({ id, user, onExpired }) {
  const [item, setItem] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [slide, setSlide] = useState(0)
  const [historyOpen, setHistoryOpen] = useState(true)

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  const refresh = useCallback(async () => {
    try {
      const found = await api(`/items/${id}`)
      // The server refuses a private history to anyone but an admin, so don't ask for it.
      const mayRead = !found.history_private || user.role === 'admin'
      setHistory(mayRead ? await api(`/items/${id}/movements`) : [])
      setItem(found)
    } catch (err) {
      handle(err)
    }
  }, [id, user.role, handle])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function send(path, options, form) {
    setError('')
    let result = null
    try {
      result = await api(path, { method: 'POST', ...options })
      form?.reset()
    } catch (err) {
      handle(err)
    }
    await refresh()
    return result
  }

  const path = <Breadcrumb id={id} />
  if (!item) {
    return (
      <>
        {path}
        {error ? <p className="error">{error}</p> : <p className="hint">Loading…</p>}
      </>
    )
  }

  // The slide on show; kept inside the range when a picture is removed.
  const shown = Math.min(slide, Math.max(item.image_ids.length - 1, 0))

  const hidden = item.quantity === null // private stock, and this user is not an admin
  const historyHidden = item.history_private && user.role !== 'admin'
  const status = item.quantity === 0 ? 'Out of stock' : item.low_stock ? 'Low stock' : 'In stock'
  const tag = (isPrivate) => <span className="tag">{isPrivate ? 'Private' : 'Public'}</span>
  const alwaysPublic = <span className="tag">Always public</span>

  function showHistory() {
    setHistoryOpen(true)
    document.getElementById('stock-history').scrollIntoView({ behavior: 'smooth' })
  }
  const last = history[0]
  const signed = (change) => (change > 0 ? `+${change}` : change)
  const when = (entry) => new Date(entry.created_at).toLocaleString()

  // Laid out like a shop's product page: the pictures, what you can do beside it, then the details.
  return (
    <>
      {path}
      {error && <p className="error">{error}</p>}

      <div className="product">
        <Slideshow item={item} shown={shown} onShow={setSlide} />

        <div className="product-side">
          <div className="product-head">
            <h1>{item.name}</h1>
            {may(user, 'can_edit_items', item) && (
              <a className="edit-button" href={`#/inventory/item/${item.id}/edit`}>
                Edit
              </a>
            )}
          </div>
          <p className="subtitle">
            SKU {item.sku} · ID {item.id}
          </p>
          {hidden ? (
            <div className="buy-box">
              <p>The stock of this item is private.</p>
            </div>
          ) : (
            <>
              <span className={item.low_stock ? 'badge low' : 'badge'}>{status}</span>

              <div className="buy-box">
                <p className="figure">
                  <strong>{item.quantity}</strong> in stock
                </p>
                <p className="hint">Reorder at {item.reorder_level}</p>
                {may(user, 'can_move_stock', item) ? (
                  <MoveStock item={item} send={send} />
                ) : (
                  <p className="hint">
                    {may(user, 'can_move_stock') ? 'You can change only the items you added.' : "You don't have permission to change stock."}
                  </p>
                )}
              </div>
            </>
          )}
          {!historyHidden && (
            <p className="fact">
              <span className="hint">Last movement</span>
              {last ? (
                <span>
                  {signed(last.change)} by {last.username}
                  <button type="button" className="link" onClick={showHistory}>
                    See all
                  </button>
                </span>
              ) : (
                <span>None yet</span>
              )}
            </p>
          )}
        </div>
      </div>

      <section className="block">
        <h2>Product details</h2>
        <div className="card panel">
          <h3>Stock {tag(item.stock_private)}</h3>
          {hidden ? (
            <p className="hint">This information is private. Only admins can see it.</p>
          ) : (
            <Details
              rows={[
                ['In stock', item.quantity],
                ['Status', status],
                ['Reorder level', item.reorder_level],
              ]}
            />
          )}
        </div>
      </section>

      <section className="card panel">
        <h3>Description {alwaysPublic}</h3>
        {item.description ? <p className="description">{item.description}</p> : <p className="hint">No description yet.</p>}
      </section>

      <section className="card panel" id="stock-history">
        <h3>
          Stock history
          <span className="panel-actions">
            {tag(item.history_private)}
            <button
              type="button"
              className="toggle"
              aria-expanded={historyOpen}
              aria-controls="history-body"
              aria-label={historyOpen ? 'Hide stock history' : 'Show stock history'}
              onClick={() => setHistoryOpen(!historyOpen)}
            >
              <span aria-hidden="true">⌄</span>
            </button>
          </span>
        </h3>
        <div id="history-body" hidden={!historyOpen}>
          {historyHidden && <p className="hint">The stock history is private. Only admins can see it.</p>}
          {!historyHidden && history.length === 0 && <p className="hint">No stock movements yet.</p>}
          {history.length > 0 && (
            <table className="history">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Change</th>
                  <th>By</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id}>
                    <td>{when(entry)}</td>
                    <td>{signed(entry.change)}</td>
                    <td>
                      <a href={personLink(entry.user_id)}>{entry.username}</a>
                    </td>
                    <td>{entry.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </>
  )
}
