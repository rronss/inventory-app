import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import { chatLink } from './itemControls.jsx'

const NOBODY = { friends: [], incoming: [], outgoing: [], blocked: [] }
// What each action asks of the server.
const REQUESTS = {
  ask: ['', 'POST'], // send a request
  accept: ['/accept', 'POST'],
  end: ['', 'DELETE'], // decline, cancel or remove
  block: ['/block', 'PUT'],
  unblock: ['/block', 'DELETE'],
}

// My friends, requests and blocked people, and what can be done about one person.
export function useFriends(onExpired) {
  const [lists, setLists] = useState(NOBODY)
  const [error, setError] = useState('')

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])
  const reload = useCallback(() => api('/friends').then(setLists).catch(handle), [handle])

  useEffect(() => {
    reload()
  }, [reload])

  const has = (list, id) => lists[list].some((person) => person.id === id)
  function statusOf(id) {
    if (has('blocked', id)) return 'blocked'
    if (has('friends', id)) return 'friends'
    if (has('incoming', id)) return 'received'
    return has('outgoing', id) ? 'sent' : 'none'
  }

  async function act(id, action) {
    setError('')
    try {
      const [path, method] = REQUESTS[action]
      await api(`/friends/${id}${path}`, { method })
    } catch (err) {
      handle(err)
    }
    await reload()
  }

  return { lists, statusOf, act, error }
}

// `listed`: the row is in a list of people, where unfriending is done through Edit, not on each row.
// `chatWith`: the person's id, to offer a Chat button when they are a friend.
export function FriendButton({ status, onAct, small, canBlock, listed, chatWith }) {
  const [asking, setAsking] = useState(false) // "Block" asks before it does it
  const button = (label, action, tone = '') => (
    <button type="button" className={`tool ${tone} ${small ? 'small' : ''}`} onClick={() => onAct(action)}>
      {label}
    </button>
  )
  return (
    <span className="friend-actions">
      {status === 'none' && button('Add friend', 'ask')}
      {status === 'sent' && (
        <>
          <span className="hint">Request sent</span>
          {button('Cancel', 'end')}
        </>
      )}
      {status === 'received' && (
        <>
          {button('Accept', 'accept', 'primary')}
          {button('Decline', 'end')}
        </>
      )}
      {status === 'friends' && (
        <>
          <span className="tag">Friends</span>
          {chatWith && (
            <a className={`tool primary ${small ? 'small' : ''}`} href={chatLink(chatWith)}>
              Chat
            </a>
          )}
          {!listed && button('Unfriend', 'end')}
        </>
      )}
      {status === 'blocked' && (
        <>
          <span className="tag">Blocked</span>
          {button('Unblock', 'unblock')}
        </>
      )}
      {canBlock && status !== 'blocked' && !asking && (
        <button type="button" className={`tool danger ${small ? 'small' : ''}`} onClick={() => setAsking(true)}>
          Block
        </button>
      )}
      {asking && status !== 'blocked' && (
        <>
          <span className="hint">Block?</span>
          <button
            type="button"
            className={`tool solid-danger ${small ? 'small' : ''}`}
            onClick={() => {
              setAsking(false)
              onAct('block')
            }}
          >
            Yes, block
          </button>
          <button type="button" className={`tool ${small ? 'small' : ''}`} onClick={() => setAsking(false)}>
            No
          </button>
        </>
      )}
    </span>
  )
}
