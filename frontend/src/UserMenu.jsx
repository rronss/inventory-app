import Avatar from './Avatar.jsx'
import useDropdown from './useDropdown.js'

// The profile icon at the right of the top bar. Clicking it opens the account's pages.
export default function UserMenu({ user, current, onSignOut }) {
  const [open, setOpen, box] = useDropdown()

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
            {link('friends', 'Friends')}
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
