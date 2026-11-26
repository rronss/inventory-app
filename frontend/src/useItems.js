import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'

// Loads items and runs changes; a sign-in that has expired logs the user out.
export default function useItems(query, onExpired) {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  const handle = useCallback((err) => (err.status === 401 ? onExpired() : setError(err.message)), [onExpired])

  const refresh = useCallback(async () => {
    try {
      setItems(await api(`/items${query}`))
    } catch (err) {
      handle(err)
    }
  }, [query, handle])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function send(path, options, form) {
    setError('')
    let result = null
    try {
      result = await api(path, { method: 'POST', ...options })
      form?.reset()
    } catch (err) {
      handle(err)
    }
    await refresh()
    return result
  }

  return { items, error, send }
}
