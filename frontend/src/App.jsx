import { useCallback, useEffect, useState } from 'react'

import { api, getToken, setToken } from './api.js'
import Home from './Home.jsx'
import Inventory from './Inventory.jsx'
import Item from './Item.jsx'
import ItemEdit from './ItemEdit.jsx'
import Movements from './Movements.jsx'
import Landing from './Landing.jsx'
import Profile from './Profile.jsx'
import Users from './Users.jsx'

const PAGES = { home: 'Home', inventory: 'Inventory', profile: 'My profile', users: 'Users' }
const INVENTORY_TABS = [
  ['', 'Items'],
  ['movements', 'Movements'],
  ['add', 'Add an item'],
]
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
  const visible = Object.entries(PAGES).filter(([key]) => key !== 'users' || isAdmin)
  // "inventory/add" is the second tab of the inventory page; "inventory/item/3" is one item's profile
  // and "inventory/item/3/edit" changes it.
  const [section, tab = '', itemId, action] = page.split('/')
  const active = visible.some(([key]) => key === section) ? section : 'home'
  const props = { user, onExpired: logOut }

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
        <button className="secondary" onClick={logOut}>
          Sign out
        </button>
      </header>
      {active === 'inventory' && (
        <nav className="subtabs" aria-label="Inventory">
          {INVENTORY_TABS.map(([key, label]) => (
            <a key={label} href={`#/inventory${key && `/${key}`}`} aria-current={(tab === 'item' ? '' : tab) === key ? 'page' : undefined}>
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
        {active === 'profile' && <Profile {...props} onChanged={loadUser} />}
        {active === 'users' && <Users {...props} />}
      </main>
    </>
  )
}
