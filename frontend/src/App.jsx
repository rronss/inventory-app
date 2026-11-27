import { useCallback, useEffect, useState } from 'react'

import Admin from './Admin.jsx'
import Alerts from './Alerts.jsx'
import { api, getToken, setToken } from './api.js'
import Brand from './Brand.jsx'
import Chats from './Chats.jsx'
import Dashboard from './Dashboard.jsx'
import Explore from './Explore.jsx'
import FriendsPage from './FriendsPage.jsx'
import Home from './Home.jsx'
import Inventory from './Inventory.jsx'
import Item from './Item.jsx'
import ItemEdit from './ItemEdit.jsx'
import Movements from './Movements.jsx'
import Person from './Person.jsx'
import Landing from './Landing.jsx'
import Profile from './Profile.jsx'
import Updates from './Updates.jsx'
import UserMenu from './UserMenu.jsx'

const PAGES = { home: 'Home', explore: 'Explore', inventory: 'Inventory', inbox: 'Inbox', profile: 'Profile', friends: 'Friends', settings: 'Settings', admin: 'Admin' }
// The rest are reached from the profile icon.
const IN_TOP_BAR = ['explore', 'inventory', 'inbox'] // the homepage opens from the app's name
// The second row of tabs, for the pages that have one.
const SUBTABS = {
  inbox: [
    ['', 'Chats'],
    ['alerts', 'Alerts'],
    ['updates', 'Updates'],
  ],
  inventory: [
    ['', 'Items'],
    ['movements', 'Movements'],
    ['overview', 'Overview'],
  ],
  admin: [
    ['', 'Users'],
    ['staff', 'Staff'],
  ],
  settings: [
    ['', 'Profile Settings'],
    ['security', 'Privacy & Security'],
  ],
}
const currentPage = () => window.location.hash.replace(/^#\/?/, '')

function Count({ n }) {
  if (!n) return null
  return (
    <span className="nav-count" aria-label={`${n} unread`}>
      {n > 99 ? '99+' : n}
    </span>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))
  const [offline, setOffline] = useState(false)
  const [page, setPage] = useState(currentPage)

  useEffect(() => {
    const onChange = () => setPage(currentPage())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  const logOut = useCallback(() => {
    setToken(null)
    setUser(null)
    window.location.hash = ''
  }, [])

  const loadUser = useCallback(async () => {
    try {
      setUser(await api('/auth/me'))
      setOffline(false)
      if (['', 'signin', 'register'].includes(currentPage())) window.location.hash = '/home'
    } catch (err) {
      // Only a refused token signs you out. A server that is restarting or unreachable does not.
      if (err.status === 401) logOut()
      else setOffline(true)
    } finally {
      setChecking(false)
    }
  }, [logOut])

  useEffect(() => {
    if (getToken()) loadUser()
  }, [loadUser])

  // The numbers on the Inbox tabs: checked on every page change, and now and then while staying on one.
  const [waiting, setWaiting] = useState({ unread: 0, messages: 0, updates: 0 })
  const countUnread = useCallback(() => {
    api('/inbox/unread')
      .then(setWaiting)
      .catch((err) => err.status === 401 && logOut())
  }, [logOut])

  useEffect(() => {
    if (!user) return undefined
    countUnread()
    const timer = setInterval(countUnread, 10000)
    return () => clearInterval(timer)
  }, [user, page, countUnread])

  if (checking) return <p className="loading">Loading…</p>
  if (!user && offline && getToken()) {
    return (
      <p className="loading">
        The server can't be reached.
        <button className="link" onClick={loadUser}>
          Try again
        </button>
      </p>
    )
  }
  if (!user) return <Landing page={page} onSignedIn={loadUser} />

  const isAdmin = user.role === 'admin'
  const visible = Object.entries(PAGES).filter(([key]) => key !== 'admin' || isAdmin)
  // "inventory/add" is the form behind the New button on Items; "inventory/item/3" is one item's profile
  // and "inventory/item/3/edit" changes it.
  const [section, tab = '', itemId, action] = page.split('/')
  // "people/3" is someone's profile. It has no tab of its own.
  const person = section === 'people' && tab
  const active = person ? 'people' : visible.some(([key]) => key === section) ? section : 'home'
  const props = { user, onExpired: logOut }
  // An item's page and the New form belong to the Items tab.
  // So does one chat, "inbox/chats/3", to the Chats tab.
  const subtab = (active === 'inventory' && ['item', 'add'].includes(tab)) || (active === 'inbox' && tab === 'chats') ? '' : tab

  return (
    <>
      <header className="topbar">
        <Brand href="#/home" />
        <nav>
          {visible
            .filter(([key]) => IN_TOP_BAR.includes(key))
            .map(([key, label]) => (
              <a key={key} href={`#/${key}`} aria-current={active === key ? 'page' : undefined}>
                {label}
                {key === 'inbox' && <Count n={waiting.unread + waiting.messages + waiting.updates} />}
              </a>
            ))}
        </nav>
        <UserMenu user={user} current={active} onSignOut={logOut} />
      </header>
      {SUBTABS[active] && (
        <nav className="subtabs" aria-label={PAGES[active]}>
          {SUBTABS[active].map(([key, label]) => (
            <a key={label} href={`#/${active}${key && `/${key}`}`} aria-current={subtab === key ? 'page' : undefined}>
              {label}
              {active === 'inbox' && <Count n={waiting[{ '': 'messages', alerts: 'unread', updates: 'updates' }[key]]} />}
            </a>
          ))}
        </nav>
      )}
      {active === 'home' && <Home />}
      <main>
        {active === 'explore' && <Explore {...props} />}
        {active === 'inbox' &&
          (tab === 'alerts' ? (
            <Alerts {...props} onRead={countUnread} />
          ) : tab === 'updates' ? (
            <Updates {...props} onRead={countUnread} />
          ) : (
            <Chats personId={tab === 'chats' ? itemId : undefined} {...props} onRead={countUnread} />
          ))}
        {active === 'inventory' &&
          (tab === 'movements' ? (
            <Movements {...props} />
          ) : tab === 'overview' ? (
            <Dashboard {...props} />
          ) : tab !== 'item' ? (
            <Inventory key={tab} tab={tab} {...props} />
          ) : action === 'edit' ? (
            <ItemEdit key={itemId} id={itemId} {...props} />
          ) : (
            <Item key={itemId} id={itemId} {...props} />
          ))}
        {(active === 'profile' || active === 'settings') && (
          <Profile key={`${active}/${tab}`} page={active} tab={tab} {...props} onChanged={loadUser} />
        )}
        {active === 'admin' && <Admin key={tab} tab={tab} {...props} />}
        {active === 'friends' && <FriendsPage {...props} />}
        {person && <Person key={tab} id={tab} {...props} />}
      </main>
    </>
  )
}
