import { useCallback, useEffect, useState } from 'react'

import Admin from './Admin.jsx'
import { api, getToken, setToken } from './api.js'
import Home from './Home.jsx'
import Inventory from './Inventory.jsx'
import Item from './Item.jsx'
import ItemEdit from './ItemEdit.jsx'
import Movements from './Movements.jsx'
import Person from './Person.jsx'
import Landing from './Landing.jsx'
import Profile from './Profile.jsx'

const PAGES = { home: 'Home', inventory: 'Inventory', profile: 'Profile', admin: 'Admin' }
// The second row of tabs, for the pages that have one.
const SUBTABS = {
  inventory: [
    ['', 'Items'],
    ['movements', 'Movements'],
  ],
  admin: [
    ['', 'Users'],
    ['staff', 'Staff'],
  ],
  profile: [
    ['', 'My profile'],
    ['edit', 'Edit profile'],
    ['security', 'Privacy & Security'],
  ],
}
const currentPage = () => window.location.hash.replace(/^#\/?/, '')

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
  const subtab = active === 'inventory' && ['item', 'add'].includes(tab) ? '' : tab

  return (
    <>
      <header className="topbar">
        <a className="brand" href="#/home">
          Inventory
        </a>
        <nav>
          {visible.map(([key, label]) => (
            <a key={key} href={`#/${key}`} aria-current={active === key ? 'page' : undefined}>
              {label}
            </a>
          ))}
        </nav>
      </header>
      {SUBTABS[active] && (
        <nav className="subtabs" aria-label={PAGES[active]}>
          {SUBTABS[active].map(([key, label]) => (
            <a key={label} href={`#/${active}${key && `/${key}`}`} aria-current={subtab === key ? 'page' : undefined}>
              {label}
            </a>
          ))}
        </nav>
      )}
      <main>
        {active === 'home' && <Home {...props} />}
        {active === 'inventory' &&
          (tab === 'movements' ? (
            <Movements {...props} />
          ) : tab !== 'item' ? (
            <Inventory key={tab} tab={tab} {...props} />
          ) : action === 'edit' ? (
            <ItemEdit key={itemId} id={itemId} {...props} />
          ) : (
            <Item key={itemId} id={itemId} {...props} />
          ))}
        {active === 'profile' && <Profile key={tab} tab={tab} {...props} onChanged={loadUser} onSignOut={logOut} />}
        {active === 'admin' && <Admin key={tab} tab={tab} {...props} />}
        {person && <Person key={tab} id={tab} {...props} />}
      </main>
    </>
  )
}
