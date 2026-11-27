import { useState } from 'react'

import Confirm from './Confirm.jsx'
import { chatLink } from './itemControls.jsx'
import useDropdown from './useDropdown.js'

// What can be done about a friendship, by where it stands: [label, action].
const FRIEND_OPTIONS = {
  none: [['Add friend', 'ask']],
  sent: [['Cancel friend request', 'end']],
  received: [
    ['Accept friend request', 'accept'],
    ['Decline friend request', 'end'],
  ],
  friends: [['Unfriend', 'end']],
  blocked: [['Unblock', 'unblock']],
}

// The three-line button on a profile. On your own it leads to your pages; on someone else's, to what you can do.
export default function ProfileMenu({ person, own, status, onAct }) {
  const [open, setOpen, box] = useDropdown()
  const [blocking, setBlocking] = useState(false)

  const link = (href, label) => (
    <li>
      <a href={href} onClick={() => setOpen(false)}>
        {label}
      </a>
    </li>
  )
  const button = (label, run, tone) => (
    <li key={label}>
      <button
        type="button"
        className={tone}
        onClick={() => {
          setOpen(false)
          run()
        }}
      >
        {label}
      </button>
    </li>
  )

  return (
    <div className="user-menu" ref={box}>
      <button type="button" className="hamburger" aria-label="Profile options" aria-expanded={open} onClick={() => setOpen(!open)}>
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>
      {open && (
        <div className="menu">
          {own ? (
            <ul>
              {link('#/settings', 'Edit profile')}
              {link('#/friends', 'Friends')}
              {link('#/settings/security', 'Privacy & Security')}
            </ul>
          ) : (
            <>
              <ul>
                {status !== 'blocked' && link(chatLink(person.id), 'Chat')}
                {FRIEND_OPTIONS[status].map(([label, action]) => button(label, () => onAct(action)))}
              </ul>
              {status !== 'blocked' && <ul className="menu-second">{button('Block', () => setBlocking(true), 'risky')}</ul>}
            </>
          )}
        </div>
      )}
      {blocking && (
        <Confirm
          title={`Do you really want to block ${person.username}?`}
          names={[[person.id, person.username, person.name]]}
          note="Neither of you can send friend requests or messages. They are not told."
          yes="Yes, block"
          onConfirm={() => {
            setBlocking(false)
            onAct('block')
          }}
          onCancel={() => setBlocking(false)}
        />
      )}
    </div>
  )
}
