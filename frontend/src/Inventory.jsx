import { useState } from 'react'

import { itemLink, MoveStock, Owner } from './itemControls.jsx'
import useItems from './useItems.js'

export default function Inventory({ tab, user, onExpired }) {
  const [lowOnly, setLowOnly] = useState(false)
  const { items, error, send } = useItems(lowOnly ? '?low=true' : '', onExpired)

  async function addItem(event) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.target))
    const body = { ...data, quantity: Number(data.quantity), reorder_level: Number(data.reorder_level) }
    if (await send('/items', { body }, event.target)) window.location.hash = '/inventory'
  }

  return (
    <>
      <h1>{tab === 'add' ? 'Add an item' : 'Items'}</h1>
      {error && <p className="error">{error}</p>}
      {tab === 'add' ? (
        <section className="card">
          <p className="hint">The new item is attached to you.</p>
          <form className="inline" onSubmit={addItem}>
            <input name="sku" placeholder="SKU" required maxLength="40" />
            <input name="name" placeholder="Name" required maxLength="120" />
            <input name="quantity" type="number" min="0" placeholder="Quantity" required />
            <input name="reorder_level" type="number" min="0" placeholder="Reorder at" required />
            <button type="submit">Add item</button>
          </form>
        </section>
      ) : (
        <section className="card">
          <label className="inline">
            <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
            Low stock only
          </label>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>SKU</th>
                <th>Name</th>
                <th>Quantity</th>
                <th>Reorder at</th>
                <th>Attached to</th>
                <th>Stock in / out</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={item.low_stock ? 'low' : ''}>
                  <td data-label="ID">{item.id}</td>
                  <td>{item.sku}</td>
                  <td className="name">
                    <a href={itemLink(item)}>{item.name}</a>
                  </td>
                  <td data-label="Quantity">{item.quantity}</td>
                  <td data-label="Reorder at">{item.reorder_level}</td>
                  <td data-label="Attached to" className="owner">
                    <Owner item={item} user={user} send={send} />
                  </td>
                  <td>
                    <MoveStock item={item} send={send} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && <p className="hint">No items to show.</p>}
        </section>
      )}
    </>
  )
}
