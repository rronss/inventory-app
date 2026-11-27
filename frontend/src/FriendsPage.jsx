import { useEffect, useRef, useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import Confirm from './Confirm.jsx'
import { FriendButton, useFriends } from './Friends.jsx'
import { personLink } from './itemControls.jsx'
import SearchBar from './SearchBar.jsx'
import Total from './Total.jsx'

// With `ticked` given, each row has a checkbox instead of its own buttons.
// `counted`: show how many, for lists whose number is not already on the page.
function People({ title, people, friends, empty, ticked, onTick, counted }) {
  if (people.length === 0 && !empty) return null
  return (
    <section className="card panel">
      <h3>
        {title} {counted && <span className="tag">{people.length}</span>}
      </h3>
      {people.length === 0 && <p className="hint">{empty}</p>}
      <ul className="friend-list">
        {people.map((person) => (
          <li key={person.id} className="friend-row">
            {ticked && (
              <input
                type="checkbox"
                aria-label={`Select ${person.username}`}
                checked={ticked.includes(person.id)}
                onChange={() => onTick(person.id)}
              />
            )}
            <Avatar user={person} small />
            <a href={personLink(person.id)}>
              {person.username} {person.name && person.name !== person.username && <small>{person.name}</small>}
            </a>
            {!ticked && (
              <FriendButton
                status={friends.statusOf(person.id)}
                onAct={(action) => friends.act(person.id, action)}
                chatWith={person.id}
                listed
                small
              />
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

// The pop-up behind "Add friend": whom to send a request to.
function AddFriend({ people, user, friends, onSent, onClose }) {
  const [problem, setProblem] = useState('')
  const dialog = useRef(null)

  useEffect(() => {
    if (!dialog.current.open) dialog.current.showModal()
  }, [])

  function escape(event) {
    event.preventDefault()
    onClose()
  }

  async function submit(event) {
    event.preventDefault()
    const typed = new FormData(event.target).get('username').trim()
    const person = people.find((other) => other.username.toLowerCase() === typed.toLowerCase())
    if (!person) return setProblem(`There is no user called "${typed}"`)
    if (person.id === user.id) return setProblem("That's your own username")
    const refused = {
      friends: `You are already friends with ${person.username}`,
      sent: `You already sent ${person.username} a request`,
      blocked: `Unblock ${person.username} first`,
    }[friends.statusOf(person.id)]
    if (refused) return setProblem(refused)
    // a person who already asked you becomes a friend at once
    const theyAsked = friends.statusOf(person.id) === 'received'
    await friends.act(person.id, 'ask')
    onSent(theyAsked ? `You and ${person.username} are now friends` : `Friend request sent to ${person.username}`)
  }

  return (
    <dialog ref={dialog} className="dialog" aria-labelledby="add-friend-title" onCancel={escape}>
      <h2 id="add-friend-title">Add friend</h2>
      <form onSubmit={submit} onChange={() => setProblem('')}>
        <label>
          Who do you want to send a friend request to?
          <input name="username" autoComplete="off" placeholder="Username" required autoFocus />
        </label>
        {problem && <p className="error">{problem}</p>}
        <div className="dialog-actions">
          <button type="button" className="tool" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="tool primary">
            Send request
          </button>
        </div>
      </form>
    </dialog>
  )
}

// What can be done to several friends at once.
const BULK = {
  end: { verb: 'unfriend', yes: 'Yes, unfriend', note: 'You can send them a request again later.' },
  block: {
    verb: 'block',
    yes: 'Yes, block',
    note: 'They stop being friends, and neither of you can send requests or messages. They are not told.',
  },
}

// Find people and add them; Edit unfriends or blocks friends.
export default function FriendsPage({ user, onExpired }) {
  const friends = useFriends(onExpired)
  const [people, setPeople] = useState([])
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const [sent, setSent] = useState('')
  const [editing, setEditing] = useState(false)
  const [ticked, setTicked] = useState([]) // ids of the ticked friends
  const [asking, setAsking] = useState(null) // 'end' or 'block', while the pop-up is open

  useEffect(() => {
    api('/people')
      .then(setPeople)
      .catch((err) => err.status === 401 && onExpired())
  }, [onExpired])

  const term = search.trim().toLowerCase()
  const found = people.filter(
    (person) => person.id !== user.id && [person.username, person.name].some((text) => text.toLowerCase().includes(term)),
  )
  const { lists } = friends
  const chosen = lists.friends.filter((person) => ticked.includes(person.id))
  const shownFriends = lists.friends.filter((person) => !term || found.some((other) => other.id === person.id))

  function stopEditing() {
    setEditing(false)
    setTicked([])
    setAsking(null)
  }

  const tick = (id) => setTicked((ids) => (ids.includes(id) ? ids.filter((other) => other !== id) : [...ids, id]))

  async function doToChosen() {
    const action = asking
    const people = chosen
    stopEditing()
    for (const person of people) await friends.act(person.id, action)
  }

  return (
    <>
      <div className="page-head">
        <h1>Friends</h1>
        <button
          type="button"
          className="tool primary"
          aria-haspopup="dialog"
          onClick={() => {
            setAdding(true)
            setSent('')
          }}
        >
          Add friend
        </button>
      </div>
      {adding && (
        <AddFriend
          people={people}
          user={user}
          friends={friends}
          onSent={(message) => {
            setSent(message)
            setAdding(false)
          }}
          onClose={() => setAdding(false)}
        />
      )}
      {sent && !friends.error && <p className="ok">{sent}</p>}
      <SearchBar value={search} onChange={setSearch} placeholder="Search people by username or name" label="Search people" />
      {friends.error && <p className="error">{friends.error}</p>}
      <Total label="Total friends" count={lists.friends.length} showing={term && !editing ? found.length : undefined}>
        {(lists.friends.length > 0 || editing) && (
          <button type="button" className="tool small" aria-pressed={editing} onClick={() => (editing ? stopEditing() : setEditing(true))}>
            {editing ? 'Done' : 'Edit'}
          </button>
        )}
      </Total>
      {editing && (
        <div className="selection">
          {chosen.length === 0 && <span className="hint">Tick the friends to change.</span>}
          {chosen.length > 0 && (
            <>
              <button type="button" className="tool small" onClick={() => setAsking('end')}>
                Unfriend ({chosen.length})
              </button>
              <button type="button" className="tool danger small" onClick={() => setAsking('block')}>
                Block ({chosen.length})
              </button>
            </>
          )}
        </div>
      )}
      {asking && (
        <Confirm
          title={`Do you really want to ${BULK[asking].verb} ${chosen.length === 1 ? 'this friend' : `these ${chosen.length} friends`}?`}
          names={chosen.map((person) => [person.id, person.username, person.name])}
          note={BULK[asking].note}
          yes={BULK[asking].yes}
          onConfirm={doToChosen}
          onCancel={() => setAsking(null)}
        />
      )}
      {editing ? (
        <People title="Your friends" people={shownFriends} friends={friends} ticked={ticked} onTick={tick} empty="No friends match." />
      ) : term ? (
        <People title="Search results" people={found} friends={friends} empty="Nobody matches your search." />
      ) : (
        <>
          <People title="Requests to you" people={lists.incoming} friends={friends} counted />
          <People
            title="Your friends"
            people={lists.friends}
            friends={friends}
            empty="No friends yet. Search for someone above."
          />
          <People title="Sent requests" people={lists.outgoing} friends={friends} counted />
          <People title="Blocked" people={lists.blocked} friends={friends} counted />
        </>
      )}
    </>
  )
}
