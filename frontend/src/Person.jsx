import { useCallback, useEffect, useState } from 'react'

import AccountControls from './AccountControls.jsx'
import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { useFriends } from './Friends.jsx'
import ItemCard from './ItemCard.jsx'
import ProfileMenu from './ProfileMenu.jsx'

const ROLES = { admin: 'Admin', staff: 'Staff' }
const STATUS = { friends: 'Friends', sent: 'Request sent', received: 'Wants to be friends', blocked: 'Blocked' }

// A person's record: enough to recognise them, and the items they added.
export default function Person({ id, user, onExpired, inProfile }) {
  const [person, setPerson] = useState(null)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const isMe = Number(id) === user.id
  const friends = useFriends(onExpired)

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  const friendship = friends.statusOf(Number(id)) // the count on the page follows an add or a remove

  useEffect(() => {
    Promise.all([api(`/people/${id}`), api(`/people/${id}/items`)])
      .then(([found, added]) => {
        setItems(added)
        setPerson(found)
      })
      .catch(handle)
  }, [id, friendship, handle])

  if (!person) return error ? <p className="error">{error}</p> : <p className="hint">Loading…</p>

  return (
    <>
      {!inProfile && (
        <div className="page-head">
          <h1>
            {person.username} {!isMe && STATUS[friends.statusOf(person.id)] && <span className="tag">{STATUS[friends.statusOf(person.id)]}</span>}
          </h1>
          <ProfileMenu
            person={person}
            own={isMe}
            status={friends.statusOf(person.id)}
            onAct={(action) => friends.act(person.id, action)}
          />
        </div>
      )}
      {friends.error && <p className="error">{friends.error}</p>}
      {error && <p className="error">{error}</p>}
      <section className="card record">
        <Avatar user={person} />
        <dl className="details-list">
          {[
            ['User ID', person.id],
            ['Username', person.username],
            ['Role', ROLES[person.role] || person.role],
            ['Bio', person.bio || '—'],
            // on your own profile the number leads to your friends
            ['Friends', isMe ? <a href="#/friends">{friends.lists.friends.length}</a> : person.friends],
          ].map(([term, value]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd className="description">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      {user.role === 'admin' && !isMe && (
        <AccountControls id={id} handle={handle} onRole={(role) => setPerson({ ...person, role })} />
      )}

      <h2 className="section-title">
        Items added <span className="tag">{items.length}</span>
      </h2>
      {items.length === 0 && <p className="card hint">No items added yet.</p>}
      <ul className="tiles">
        {items.map((item) => (
          <ItemCard key={item.id} item={item}>
            <small className="tile-id">
              ID {item.id} · SKU {item.sku}
            </small>
          </ItemCard>
        ))}
      </ul>
    </>
  )
}
