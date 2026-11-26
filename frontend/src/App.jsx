import { useCallback, useEffect, useState } from 'react'

import { api, getToken, setToken } from './api.js'
import Inventory from './Inventory.jsx'
import Login from './Login.jsx'

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))

  const signOut = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const loadUser = useCallback(async () => {
    try {
      setUser(await api('/auth/me'))
    } catch {
      signOut()
    } finally {
      setChecking(false)
    }
  }, [signOut])

  useEffect(() => {
    if (getToken()) loadUser()
  }, [loadUser])

  if (checking) return <p className="center">Loading…</p>
  if (!user) return <Login onSignedIn={loadUser} />

  return (
    <main>
      <header>
        <h1>Inventory</h1>
        <span>
          {user.email} ({user.role})
        </span>
        <button className="secondary" onClick={signOut}>
          Sign out
        </button>
      </header>
      <Inventory isAdmin={user.role === 'admin'} onExpired={signOut} />
    </main>
  )
}
