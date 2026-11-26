import { useEffect, useRef, useState } from 'react'

import Avatar from './Avatar.jsx'

// The profile icon at the right of the top bar. Clicking it opens the account's pages.
export default function UserMenu({ user, current, onSignOut }) {
  const [open, setOpen] = useState(false)
  const box = useRef(null)

  // a click anywhere else, or Esc, closes it
  useEffect(() => {
    if (!open) return undefined
    const away = (event) => !box.current.contains(event.target) && setOpen(false)
    const escape = (event) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', away)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', away)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  const link = (key, label) => (
    <li key={key}>
      <a href={`#/${key}`} aria-current={current === key ? 'page' : undefined} onClick={() => setOpen(false)}>
        {label}
      </a>
    </li>
  )

  return (
    <div className="user-menu" ref={box}>
      <button type="button" className="avatar-button" aria-label="Account menu" aria-expanded={open} onClick={() => setOpen(!open)}>
        <Avatar user={user} small />
      </button>
      {open && (
        <div className="menu">
          <ul>
            {link('profile', 'Profile')}
            {link('settings', 'Settings')}
          </ul>
          <ul className="menu-second">
            {user.role === 'admin' && link('admin', 'Admin')}
            <li>
              <button type="button" onClick={onSignOut}>
                Log out
              </button>
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}
