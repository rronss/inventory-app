import { useEffect, useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { itemLink, personLink } from './itemControls.jsx'
import { Picture } from './itemImage.jsx'

const day = (date) => new Date(date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

function statusOf(item) {
  if (item.quantity === 0) return { label: 'Out of stock', tone: 'low' }
  if (item.low_stock) return { label: 'Low stock', tone: 'low' }
  return { label: 'In stock', tone: '' }
}

// Every public item, newest first.
export default function Explore({ user, onExpired }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/explore')
      .then(setItems)
      .catch((err) => (err.status === 401 ? onExpired() : setError(err.message)))
  }, [onExpired])

  return (
    <>
      <h1>Explore</h1>
      <p className="hint">
        Every public item{items ? `: ${items.length}` : ''}.
      </p>
      {error && <p className="error">{error}</p>}
      {items === null && !error && <p className="hint">Loading…</p>}
      {items?.length === 0 && <p className="card hint">No public items yet.</p>}
      <ul className="tiles">
        {items?.map((item) => (
          <li key={item.id} className="tile">
            <a className="tile-picture" href={itemLink(item)} aria-label={item.name}>
              {item.image_ids.length > 0 ? (
                <Picture itemId={item.id} imageId={item.image_ids[0]} alt="" />
              ) : (
                <span className="hint">No image</span>
              )}
              <span className={`badge ${statusOf(item).tone}`}>{statusOf(item).label}</span>
            </a>
            <a className="tile-name" href={itemLink(item)}>
              {item.name}
            </a>
            <p className={`tile-count ${statusOf(item).tone}`}>
              <strong>{item.quantity}</strong> in stock
            </p>
            <div className="tile-by">
              {item.added_by_id ? (
                <Avatar user={{ id: item.added_by_id, username: item.added_by, photo_version: item.added_by_photo_version }} small />
              ) : (
                <span className="avatar small" aria-hidden="true">
                  ?
                </span>
              )}
              <div>
                {item.added_by_id ? (
                  <a href={personLink(item.added_by_id)}>{item.added_by_id === user.id ? 'You' : item.added_by}</a>
                ) : (
                  <span>Unknown</span>
                )}
                <small title={item.created_at ? new Date(item.created_at).toLocaleString() : undefined}>
                  {item.created_at ? `Added ${day(item.created_at)}` : 'Date not recorded'}
                </small>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </>
  )
}
