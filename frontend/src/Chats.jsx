import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from './api.js'
import Avatar from './Avatar.jsx'
import { useFriends } from './Friends.jsx'
import { chatLink, personLink } from './itemControls.jsx'
import SearchBar from './SearchBar.jsx'
import Total from './Total.jsx'

const EVERY = 5000 // how often an open chat, or the list of chats, looks for new messages
const when = (date) => new Date(date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })

function useErrors(onExpired) {
  const [error, setError] = useState('')
  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])
  const clear = useCallback(() => setError(''), [])
  return [error, handle, clear]
}

// Runs now and then again every few seconds, until the page is left.
function useRepeat(load) {
  useEffect(() => {
    load()
    const timer = setInterval(load, EVERY)
    return () => clearInterval(timer)
  }, [load])
}

// The form that drops down under "New": who to write to, and the first message.
function NewChat({ people, user, onExpired, onClose }) {
  const [error, handle, clear] = useErrors(onExpired)
  const [problem, setProblem] = useState('')
  const sending = useRef(false)

  async function submit(event) {
    event.preventDefault()
    const data = new FormData(event.target)
    const typed = data.get('username').trim()
    const text = data.get('text').trim()
    const person = people.find((other) => other.username.toLowerCase() === typed.toLowerCase())
    clear()
    if (!person) return setProblem(`There is no user called "${typed}"`)
    if (person.id === user.id) return setProblem("That's your own username")
    if (!text) return setProblem('Write a message first')
    if (sending.current) return
    sending.current = true
    try {
      await api(`/messages/${person.id}`, { method: 'POST', body: { text } })
      window.location.hash = chatLink(person.id)
    } catch (err) {
      handle(err)
    } finally {
      sending.current = false
    }
  }

  return (
    <form className="card new-chat" onSubmit={submit} onChange={() => setProblem('')}>
      <label>
        User
        <input name="username" list="usernames" autoComplete="off" placeholder="Username" required autoFocus />
      </label>
      <datalist id="usernames">
        {people
          .filter((person) => person.id !== user.id)
          .map((person) => (
            <option key={person.id} value={person.username}>
              {person.name}
            </option>
          ))}
      </datalist>
      <label>
        Message
        <textarea name="text" rows="3" maxLength="1000" placeholder="Write your message" required />
      </label>
      {(problem || error) && <p className="error">{problem || error}</p>}
      <div className="dialog-actions">
        <button type="button" className="tool" onClick={onClose}>
          Cancel
        </button>
        <button type="submit" className="tool primary">
          Send
        </button>
      </div>
    </form>
  )
}

function ChatList({ user, onExpired, onRead }) {
  const [rows, setRows] = useState(null)
  const [people, setPeople] = useState([])
  const [writing, setWriting] = useState(false)
  const [search, setSearch] = useState('')
  const [error, handle, clear] = useErrors(onExpired)

  useEffect(() => {
    api('/people').then(setPeople).catch(handle)
  }, [handle])

  useRepeat(
    useCallback(() => {
      api('/messages')
        .then((found) => {
          setRows(found)
          clear()
          onRead() // keep the number on the tabs in step with the list
        })
        .catch(handle)
    }, [handle, clear, onRead]),
  )

  // The person's username or name, or the words of the last message.
  const term = search.trim().toLowerCase()
  const shown = rows?.filter(
    (row) => !term || [row.person.username, row.person.name, row.last_text].some((text) => text.toLowerCase().includes(term)),
  )

  return (
    <>
      <div className="page-head">
        <h1>Chats</h1>
        <button type="button" className="tool primary" aria-expanded={writing} onClick={() => setWriting(!writing)}>
          New
        </button>
      </div>
      {writing && <NewChat people={people} user={user} onExpired={onExpired} onClose={() => setWriting(false)} />}
      {error && <p className="error">{error}</p>}
      <SearchBar value={search} onChange={setSearch} placeholder="Search chats by person or last message" label="Search chats" />
      {rows && <Total label="Total chats" count={rows.length} showing={term ? shown.length : undefined} />}
      <section className="card">
        {rows === null && !error && <p className="hint">Loading…</p>}
        {rows?.length > 0 && shown.length === 0 && <p className="hint">No chats match your search.</p>}
        {rows?.length === 0 && <p className="hint">No chats yet. Press New to start one.</p>}
        <ul className="rows">
          {shown?.map((row) => (
            <li key={row.person.id}>
              <a className="row" href={chatLink(row.person.id)}>
                <Avatar user={row.person} small />
                <span className="preview">
                  <strong>{row.person.username}</strong>
                  <small>
                    {row.last_mine ? 'You: ' : ''}
                    {row.last_text}
                  </small>
                </span>
                <span>
                  <small className="chat-time">{when(row.last_at)}</small>{' '}
                  {row.unread > 0 && <span className="nav-count">{row.unread}</span>} <span aria-hidden="true">›</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}

function Chat({ id, user, onExpired, onRead }) {
  const [person, setPerson] = useState(null)
  const [messages, setMessages] = useState(null)
  const [text, setText] = useState('')
  const [error, handle, clear] = useErrors(onExpired)
  const scroller = useRef(null)
  const seen = useRef(0) // the newest incoming message already marked as read
  const sending = useRef(false)
  const friends = useFriends(onExpired)

  useEffect(() => {
    api(`/people/${id}`).then(setPerson).catch(handle)
  }, [id, handle])

  const load = useCallback(async () => {
    try {
      const found = await api(`/messages/${id}`)
      setMessages(found)
      const incoming = found.filter((message) => !message.mine).at(-1)
      if (incoming && incoming.id > seen.current) {
        await api(`/messages/${id}/read`, { method: 'POST' })
        seen.current = incoming.id
        onRead()
      }
    } catch (err) {
      handle(err)
    }
  }, [id, handle, onRead])

  useRepeat(load)

  // Follow the conversation: down to the newest message whenever one arrives.
  const newest = messages?.at(-1)?.id
  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight
  }, [newest])

  async function send(event) {
    event.preventDefault()
    if (!text.trim() || sending.current) return
    sending.current = true // one message, however fast Enter is pressed
    clear()
    try {
      await api(`/messages/${id}`, { method: 'POST', body: { text } })
      setText('')
      await load()
    } catch (err) {
      handle(err) // what was typed stays in the box
    } finally {
      sending.current = false
    }
  }

  return (
    <>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <a href="#/inbox">Chats</a>
        <span aria-hidden="true">&gt;</span>
        <span aria-current="page">{person?.username || '…'}</span>
      </nav>
      {error && <p className="error">{error}</p>}
      <section className="card">
        {person && (
          <a className="chat-with" href={personLink(person.id)}>
            <Avatar user={person} small />
            <strong>{person.username}</strong>
          </a>
        )}
        <div className="chat" ref={scroller} aria-live="polite">
          {messages?.length === 0 && <p className="hint">No messages yet. Say hello.</p>}
          {messages?.map((message) => (
            <p key={message.id} className={message.mine ? 'bubble mine' : 'bubble'}>
              {message.text}
              <small>{when(message.created_at)}</small>
            </p>
          ))}
        </div>
        {user.chat_from === 'friends' && person && friends.statusOf(person.id) !== 'friends' && (
          <p className="hint">{person.username} can't reply: you accept messages from friends only.</p>
        )}
        <form className="composer" onSubmit={send}>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength="1000"
            placeholder="Write a message"
            aria-label="Message"
            autoComplete="off"
          />
          <button type="submit">Send</button>
        </form>
      </section>
    </>
  )
}

export default function Chats({ personId, ...props }) {
  return personId ? <Chat key={personId} id={personId} {...props} /> : <ChatList {...props} />
}
