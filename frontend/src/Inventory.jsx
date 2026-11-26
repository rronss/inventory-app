import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'

export default function Inventory({ isAdmin, onExpired }) {
  const [items, setItems] = useState([])
  const [lowOnly, setLowOnly] = useState(false)
  const [error, setError] = useState('')

  const handle = useCallback(
    (err) => (err.status === 401 ? onExpired() : setError(err.message)),
    [onExpired],
  )

  const refresh = useCallback(async () => {
    try {
      setItems(await api(`/items${lowOnly ? '?low=true' : ''}`))
    } catch (err) {
      handle(err)
    }
  }, [lowOnly, handle])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function send(path, body, form) {
    setError('')
    try {
      await api(path, { method: 'POST', body })
      form?.reset()
      await refresh()
    } catch (err) {
      handle(err)
    }
  }

  function move(item, direction, event) {
    const amount = Number(new FormData(event.currentTarget.form).get('amount'))
    if (amount > 0) send(`/items/${item.id}/movements`, { change: direction * amount }, event.currentTarget.form)
  }

  function addItem(event) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.target))
    send(
      '/items',
      { ...data, quantity: Number(data.quantity), reorder_level: Number(data.reorder_level) },
      event.target,
    )
  }

  return (
    <>
      {error && <p className="error">{error}</p>}
      <section className="card">
        <label className="inline">
          <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
          Low stock only
        </label>
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Quantity</th>
              <th>Reorder at</th>
              <th>Stock in / out</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className={item.low_stock ? 'low' : ''}>
                <td>{item.sku}</td>
                <td>{item.name}</td>
                <td>{item.quantity}</td>
                <td>{item.reorder_level}</td>
                <td>
                  <form className="inline" onSubmit={(e) => e.preventDefault()}>
                    <input name="amount" type="number" min="1" placeholder="qty" aria-label={`Amount of ${item.name}`} />
                    <button type="button" onClick={(e) => move(item, 1, e)}>
                      In
                    </button>
                    <button type="button" className="secondary" onClick={(e) => move(item, -1, e)}>
                      Out
                    </button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="hint">No items to show.</p>}
      </section>

      {isAdmin && (
        <form className="card inline" onSubmit={addItem}>
          <input name="sku" placeholder="SKU" required maxLength="40" />
          <input name="name" placeholder="Name" required maxLength="120" />
          <input name="quantity" type="number" min="0" placeholder="Quantity" required />
          <input name="reorder_level" type="number" min="0" placeholder="Reorder at" required />
          <button type="submit">Add item</button>
        </form>
      )}
    </>
  )
}
