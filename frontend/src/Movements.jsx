import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'

const PAGE = 50

// Every stock change, whatever the item, newest first.
export default function Movements({ onExpired }) {
  const [rows, setRows] = useState(null)
  const [more, setMore] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(
    async (before) => {
      try {
        const page = await api(`/movements?limit=${PAGE}${before ? `&before=${before}` : ''}`)
        setRows((shown) => (before ? [...shown, ...page] : page))
        setMore(page.length === PAGE)
      } catch (err) {
        if (err.status === 401) onExpired()
        else setError(err.message)
      }
    },
    [onExpired],
  )

  useEffect(() => {
    load()
  }, [load])

  return (
    <>
      <h1>Movements</h1>
      {error && <p className="error">{error}</p>}
      <section className="card">
        {rows === null && !error && <p className="hint">Loading…</p>}
        {rows?.length === 0 && <p className="hint">No stock movements yet.</p>}
        {rows?.length > 0 && (
          <table className="history">
            <thead>
              <tr>
                <th>Date</th>
                <th>Item</th>
                <th>Change</th>
                <th>By</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                  <td>
                    <a href={`#/inventory/item/${row.item_id}`}>{row.item_name}</a>
                  </td>
                  <td>{row.change > 0 ? `+${row.change}` : row.change}</td>
                  <td>{row.username}</td>
                  <td>{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {more && (
          <p>
            <button type="button" className="secondary" onClick={() => load(rows[rows.length - 1].id)}>
              Show older
            </button>
          </p>
        )}
      </section>
    </>
  )
}
