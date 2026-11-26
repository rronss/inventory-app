import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import Breadcrumb from './Breadcrumb.jsx'
import { may } from './itemControls.jsx'
import { IMAGE_TYPES, imageProblem, MAX_IMAGES, Picture } from './itemImage.jsx'

const PRIVACY = [
  ['stock_private', 'Stock (in stock, status, reorder level)'],
  ['history_private', 'Stock history'],
]

// Change what an item is. Its quantity changes only through stock in and out, so the history stays true.
export default function ItemEdit({ id, user, onExpired }) {
  const [item, setItem] = useState(null)
  const [error, setError] = useState('')
  const [privacySaved, setPrivacySaved] = useState(false)

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  useEffect(() => {
    api(`/items/${id}`).then(setItem).catch(handle)
  }, [id, handle])

  async function send(path, options) {
    setError('')
    try {
      return await api(path, { method: 'POST', ...options })
    } catch (err) {
      handle(err)
      return null
    }
  }

  async function save(event) {
    event.preventDefault()
    const body = Object.fromEntries(new FormData(event.target))
    if ('reorder_level' in body) body.reorder_level = Number(body.reorder_level)
    if (await send(`/items/${id}`, { method: 'PATCH', body })) window.location.hash = `/inventory/item/${id}`
  }

  async function savePrivacy(event) {
    event.preventDefault()
    const data = new FormData(event.target)
    const body = Object.fromEntries(PRIVACY.map(([field]) => [field, data.get(field) === 'private']))
    const updated = await send(`/items/${id}`, { method: 'PATCH', body })
    if (!updated) return
    setItem(updated)
    setPrivacySaved(true)
  }

  async function upload(event) {
    const files = [...event.target.files]
    event.target.value = ''
    const problem = files.map(imageProblem).find(Boolean)
    if (problem) {
      setError(problem)
      return
    }
    for (const file of files) {
      const updated = await send(`/items/${id}/images`, { body: file })
      if (!updated) return
      setItem(updated)
    }
  }

  async function remove(imageId) {
    const updated = await send(`/items/${id}/images/${imageId}`, { method: 'DELETE' })
    if (updated) setItem(updated)
  }

  return (
    <>
      <Breadcrumb id={id} editing />
      <h1>Edit {item?.name}</h1>
      {error && <p className="error">{error}</p>}
      {!item && !error && <p className="hint">Loading…</p>}

      {item && !may(user, 'can_edit_items') && <p className="hint">You don't have permission to edit items.</p>}
      {item && may(user, 'can_edit_items') && (
        <>
          <form className="card edit-form" onSubmit={save}>
            <h2>Details</h2>
            <label>
              Name
              <input name="name" defaultValue={item.name} maxLength="120" required />
            </label>
            <label>
              SKU
              <input name="sku" defaultValue={item.sku} maxLength="40" required />
            </label>
            {item.reorder_level !== null && (
              <label>
                Reorder level
                <input name="reorder_level" type="number" min="0" defaultValue={item.reorder_level} required />
              </label>
            )}
            <label>
              Description
              <textarea name="description" defaultValue={item.description} maxLength="1000" rows="5" />
            </label>
            <div className="form-actions">
              <button type="submit">Save changes</button>
              <a href={`#/inventory/item/${id}`}>Cancel</a>
            </div>
          </form>

          <form className="card edit-form" onSubmit={savePrivacy} onChange={() => setPrivacySaved(false)}>
            <h2>Privacy</h2>
            <p className="hint">Private means only admins can see it. SKU, Item ID and description are always public.</p>
            {PRIVACY.map(([field, label]) => (
              <label key={field}>
                {label}
                <select name={field} defaultValue={item[field] ? 'private' : 'public'} disabled={user.role !== 'admin'}>
                  <option value="public">Public: every signed-in user sees it</option>
                  <option value="private">Private: only admins see it</option>
                </select>
              </label>
            ))}
            {user.role === 'admin' ? (
              <button type="submit">Save privacy</button>
            ) : (
              <p className="hint">Only an admin can change these.</p>
            )}
            {privacySaved && <p className="ok">Privacy saved</p>}
          </form>

          <section className="card edit-form">
            <h2>Images</h2>
            <p className="hint">Adding and removing an image takes effect at once.</p>
            {item.image_ids.length === 0 && <p className="hint">No images yet.</p>}
            <ul className="thumbs">
              {item.image_ids.map((imageId, index) => (
                <li key={imageId}>
                  <Picture itemId={item.id} imageId={imageId} alt={`${item.name}, picture ${index + 1}`} />
                  <button type="button" className="secondary" onClick={() => remove(imageId)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
            {item.image_ids.length < MAX_IMAGES && (
              <label>
                Add images (up to {MAX_IMAGES}; PNG, JPEG or WebP, 2 MB each)
                <input type="file" accept={IMAGE_TYPES} multiple onChange={upload} />
              </label>
            )}
          </section>
        </>
      )}
    </>
  )
}
