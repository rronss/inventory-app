import { useEffect, useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { FriendButton, useFriends } from './Friends.jsx'
import ItemCard from './ItemCard.jsx'
import { personLink } from './itemControls.jsx'
import SearchBar from './SearchBar.jsx'
import Total from './Total.jsx'

const day = (date) => new Date(date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

// The server sends newest first, so "Recents" is that order as it comes.
const VIEWS = [
  ['recents', 'Recents'],
  ['all', 'All items'], // A to Z
  ['friends', 'Only friends'],
  ['mine', 'My items'],
]
const NOTHING = {
  recents: 'No public items yet.',
  all: 'No public items yet.',
  friends: 'No items from friends yet. Add someone as a friend from their card.',
  mine: "You haven't added any public items yet.",
}

// Every public item, newest first.
export default function Explore({ user, onExpired }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('recents')
  const friends = useFriends(onExpired)

  useEffect(() => {
    api('/explore')
      .then(setItems)
      .catch((err) => (err.status === 401 ? onExpired() : setError(err.message)))
  }, [onExpired])

  // Name, SKU or the person who added it contains the words, or the ID is the number typed.
  const term = search.trim().toLowerCase()
  let filtered = items
  if (filter === 'all') filtered = items && [...items].sort((one, other) => one.name.localeCompare(other.name))
  if (filter === 'friends') filtered = items?.filter((item) => friends.statusOf(item.added_by_id) === 'friends')
  if (filter === 'mine') filtered = items?.filter((item) => item.added_by_id === user.id)
  const shown = filtered?.filter(
    (item) =>
      !term ||
      [item.name, item.sku, item.added_by || ''].some((text) => text.toLowerCase().includes(term)) ||
      String(item.id) === term.replace(/^id\s*/, ''),
  )

  return (
    <>
      <div className="page-head">
        <h1>Explore</h1>
        <select className="view-list" aria-label="Filter items" value={filter} onChange={(e) => setFilter(e.target.value)}>
          {VIEWS.map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <SearchBar
        value={search}
        onChange={setSearch}
        placeholder="Search items by name, SKU or person"
        label="Search public items"
      />
      {items && (
        <Total label="Total items" count={items.length} showing={term || ['friends', 'mine'].includes(filter) ? shown.length : undefined} />
      )}
      {friends.error && <p className="error">{friends.error}</p>}
      {error && <p className="error">{error}</p>}
      {items === null && !error && <p className="hint">Loading…</p>}
      {items && filtered.length === 0 && <p className="card hint">{NOTHING[filter]}</p>}
      {filtered?.length > 0 && shown.length === 0 && <p className="card hint">No items match your search.</p>}
      <ul className="tiles">
        {shown?.map((item) => (
          <ItemCard key={item.id} item={item}>
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
            {item.added_by_id && item.added_by_id !== user.id && (
              <FriendButton
                status={friends.statusOf(item.added_by_id)}
                onAct={(action) => friends.act(item.added_by_id, action)}
                small
              />
            )}
          </ItemCard>
        ))}
      </ul>
    </>
  )
}
