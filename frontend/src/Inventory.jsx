import { useState } from 'react'

import { itemLink } from './itemControls.jsx'
import { IMAGE_TYPES, imageProblem, MAX_IMAGES } from './itemImage.jsx'
import useItems from './useItems.js'

export default function Inventory({ tab, onExpired }) {
  const [lowOnly, setLowOnly] = useState(false)
  const [imageError, setImageError] = useState('')
  const { items, error, send } = useItems(lowOnly ? '?low=true' : '', onExpired)

  async function addItem(event) {
    event.preventDefault()
    const form = event.target
    const { images, ...data } = Object.fromEntries(new FormData(form))
    const files = new FormData(form).getAll('images').filter((file) => file.size)
    const problem =
      files.length > MAX_IMAGES ? `Choose up to ${MAX_IMAGES} images` : files.map(imageProblem).find(Boolean) || ''
    setImageError(problem)
    if (problem) return
    const body = { ...data, quantity: Number(data.quantity), reorder_level: Number(data.reorder_level) }
    const created = await send('/items', { body }, form)
    if (!created) return
    for (const file of files) {
      if (!(await send(`/items/${created.id}/images`, { body: file }))) {
        setImageError("The item was added, but not all its images. Add them on the item's page.")
        return
      }
    }
    window.location.hash = '/inventory'
  }

  return (
    <>
      <h1>{tab === 'add' ? 'Add an item' : 'Items'}</h1>
      {error && <p className="error">{error}</p>}
      {imageError && <p className="error">{imageError}</p>}
      {tab === 'add' ? (
        <section className="card">
          <form className="inline" onSubmit={addItem}>
            <input name="sku" placeholder="SKU" required maxLength="40" />
            <input name="name" placeholder="Name" required maxLength="120" />
            <input name="quantity" type="number" min="0" placeholder="Quantity" required />
            <input name="reorder_level" type="number" min="0" placeholder="Reorder at" required />
            <textarea name="description" placeholder="Description (optional)" aria-label="Description" maxLength="1000" rows="3" />
            <label className="file">
              Images (optional): up to {MAX_IMAGES}; PNG, JPEG or WebP, 2 MB each
              <input name="images" type="file" accept={IMAGE_TYPES} multiple />
            </label>
            <button type="submit">Add item</button>
          </form>
        </section>
      ) : (
        <section className="card">
          <label className="inline">
            <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
            Low stock only
          </label>
          <ul className="rows">
            {items.map((item) => (
              <li key={item.id}>
                <a href={itemLink(item)} className={item.low_stock ? 'low' : ''}>
                  <span>
                    {item.name} <small>ID {item.id}</small>
                  </span>
                  <span>
                    {item.quantity === null ? 'Private' : `${item.quantity} in stock${item.low_stock ? ', low' : ''}`}{' '}
                    {item.stock_private && item.quantity !== null && <span className="tag">Private</span>}{' '}
                    <span aria-hidden="true">›</span>
                  </span>
                </a>
              </li>
            ))}
          </ul>
          {items.length === 0 && <p className="hint">No items to show.</p>}
        </section>
      )}
    </>
  )
}
