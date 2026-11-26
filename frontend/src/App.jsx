import { useCallback, useEffect, useState } from 'react'

import { api, getToken, setToken } from './api.js'
import Home from './Home.jsx'
import Inventory from './Inventory.jsx'
import Item from './Item.jsx'
import Landing from './Landing.jsx'
import Profile from './Profile.jsx'
import Users from './Users.jsx'

const PAGES = { home: 'Home', inventory: 'Inventory', profile: 'My profile', users: 'Users' }
const INVENTORY_TABS = [
  ['', 'Items'],
  ['add', 'Add an item'],
]
const currentPage = () => window.location.hash.replace(/^#\/?/, '')

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))
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
      if (['', 'signin', 'register'].includes(currentPage())) window.location.hash = '/home'
    } catch {
      logOut()
    } finally {
      setChecking(false)
    }
  }, [logOut])

  useEffect(() => {
    if (getToken()) loadUser()
  }, [loadUser])

  if (checking) return <p className="loading">Loading…</p>
  if (!user) return <Landing page={page} onSignedIn={loadUser} />

  const isAdmin = user.role === 'admin'
  const visible = Object.entries(PAGES).filter(([key]) => key !== 'users' || isAdmin)
  // "inventory/add" is the second tab of the inventory page; "inventory/item/3" is one item's profile.
  const [section, tab = '', itemId] = page.split('/')
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
          (tab === 'item' ? <Item key={itemId} id={itemId} {...props} /> : <Inventory key={tab} tab={tab} {...props} />)}
        {active === 'profile' && <Profile {...props} onChanged={loadUser} />}
        {active === 'users' && <Users {...props} />}
      </main>
    </>
  )
}
