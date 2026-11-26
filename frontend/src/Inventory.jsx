import { useState } from 'react'

import ConfirmRemove from './ConfirmRemove.jsx'
import { itemLink, may } from './itemControls.jsx'
import { IMAGE_TYPES, imageProblem, MAX_IMAGES } from './itemImage.jsx'
import useItems from './useItems.js'

export default function Inventory({ tab, user, onExpired }) {
  const [lowOnly, setLowOnly] = useState(false)
  const [search, setSearch] = useState('')
  const [imageError, setImageError] = useState('')
  const [selecting, setSelecting] = useState(false)
  const [selected, setSelected] = useState([]) // ids of the ticked items
  const [confirming, setConfirming] = useState(false)
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

  // Changing what is listed, or leaving select mode, starts the selection again.
  function clearSelection() {
    setSelected([])
    setConfirming(false)
  }

  function toggle(id) {
    setSelected((ids) => (ids.includes(id) ? ids.filter((other) => other !== id) : [...ids, id]))
    setConfirming(false)
  }

  async function removeSelected() {
    const ids = selected
    clearSelection()
    for (const id of ids) await send(`/items/${id}`, { method: 'DELETE' })
  }

  // Name or SKU contains the words, or the ID is the number typed ("2" or "ID 2").
  const term = search.trim().toLowerCase()
  const shown = items.filter(
    (item) =>
      !term ||
      item.name.toLowerCase().includes(term) ||
      item.sku.toLowerCase().includes(term) ||
      String(item.id) === term.replace(/^id\s*/, ''),
  )
  const ticked = items.filter((item) => selected.includes(item.id))

  const summary = (item) => (
    <>
      <span>
        {item.name} <small>ID {item.id}</small>
      </span>
      <span>
        {item.quantity === null ? 'Private' : `${item.quantity} in stock${item.low_stock ? ', low' : ''}`}{' '}
        {item.stock_private && item.quantity !== null && <span className="tag">Private</span>}{' '}
        {!selecting && <span aria-hidden="true">›</span>}
      </span>
    </>
  )

  return (
    <>
      {tab === 'add' ? (
        <>
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <a href="#/inventory">Items</a>
            <span aria-hidden="true">&gt;</span>
            <span aria-current="page">New</span>
          </nav>
          <h1>New</h1>
        </>
      ) : (
        <div className="page-head">
          <h1>Items</h1>
          {may(user, 'can_add_items') && (
            <a className="tool primary" href="#/inventory/add">
              New
            </a>
          )}
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {imageError && <p className="error">{imageError}</p>}
      {tab === 'add' && !may(user, 'can_add_items') ? (
        <p className="hint">You don't have permission to add items.</p>
      ) : tab === 'add' ? (
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
            <button type="submit">Add</button>
          </form>
        </section>
      ) : (
        <>
          <section className="card panel">
            <h3>Filter</h3>
            <input
              type="search"
              className="search"
              placeholder="Search by name, SKU or ID"
              aria-label="Search items"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="filter-bar">
              <label className="inline">
                <input
                  type="checkbox"
                  checked={lowOnly}
                  onChange={(e) => {
                    setLowOnly(e.target.checked)
                    clearSelection()
                  }}
                />
                Low stock only
              </label>
              {user.role === 'admin' && (
                <button
                  type="button"
                  className="tool"
                  aria-pressed={selecting}
                  onClick={() => {
                    setSelecting(!selecting)
                    clearSelection()
                  }}
                >
                  {selecting ? 'Done' : 'Select'}
                </button>
              )}
            </div>
            {/* everything about the selection goes on a line of its own, so the button above stays put */}
            {selecting && (
              <div className="selection">
                {selected.length === 0 && <span className="hint">Tick the items to remove.</span>}
                {selected.length > 0 && (
                  <>
                    <span>{selected.length} selected</span>
                    <button type="button" className="tool danger" onClick={() => setConfirming(true)}>
                      Remove ({selected.length})
                    </button>
                  </>
                )}
              </div>
            )}
            {confirming && <ConfirmRemove items={ticked} onConfirm={removeSelected} onCancel={() => setConfirming(false)} />}
          </section>

          <section className="card panel">
            <h3>Inventory</h3>
            <ul className="rows">
              {shown.map((item) => (
                <li key={item.id}>
                  {selecting ? (
                    <label className={item.low_stock ? 'row low' : 'row'}>
                      <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggle(item.id)} />
                      {summary(item)}
                    </label>
                  ) : (
                    <a href={itemLink(item)} className={item.low_stock ? 'row low' : 'row'}>
                      {summary(item)}
                    </a>
                  )}
                </li>
              ))}
            </ul>
            {shown.length === 0 && <p className="hint">{term ? 'No items match your search.' : 'No items to show.'}</p>}
          </section>
        </>
      )}
    </>
  )
}
