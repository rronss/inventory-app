import { useCallback, useEffect, useState } from 'react'

import AccountControls from './AccountControls.jsx'
import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { itemLink } from './itemControls.jsx'

const ROLES = { admin: 'Admin', staff: 'Staff' }

// A person's record: enough to recognise them, and the items they added.
export default function Person({ id, user, onExpired }) {
  const [person, setPerson] = useState(null)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const isMe = Number(id) === user.id

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  useEffect(() => {
    Promise.all([api(`/people/${id}`), api(`/people/${id}/items`)])
      .then(([found, added]) => {
        setItems(added)
        setPerson(found)
      })
      .catch(handle)
  }, [id, handle])

  if (!person) return error ? <p className="error">{error}</p> : <p className="hint">Loading…</p>

  return (
    <>
      {!isMe && <h1>{person.name || person.username}</h1>}
      {error && <p className="error">{error}</p>}
      <section className="card record">
        <Avatar user={person} />
        <dl className="details-list">
          {[
            ['Name', person.name || '—'],
            ['Username', person.username],
            ['Role', ROLES[person.role] || person.role],
            ['About', person.bio || '—'],
          ].map(([term, value]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd className="description">{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      {isMe && (
        <p>
          <a className="tool" href="#/profile/edit">
            Edit profile
          </a>
        </p>
      )}

      {user.role === 'admin' && !isMe && (
        <AccountControls id={id} handle={handle} onRole={(role) => setPerson({ ...person, role })} />
      )}

      <section className="card panel">
        <h3>
          Items added <span className="tag">{items.length}</span>
        </h3>
        {items.length === 0 && <p className="hint">No items added yet.</p>}
        <ul className="rows">
          {items.map((item) => (
            <li key={item.id}>
              <a className={item.low_stock ? 'row low' : 'row'} href={itemLink(item)}>
                <span>
                  {item.name} <small>ID {item.id}</small>
                </span>
                <span>
                  {item.quantity === null ? 'Private' : `${item.quantity} in stock`} <span aria-hidden="true">›</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
