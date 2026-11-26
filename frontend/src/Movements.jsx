import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'
import { personLink } from './itemControls.jsx'

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
      <section className="card table-card">
        {rows === null && !error && <p className="hint">Loading…</p>}
        {rows?.length === 0 && <p className="hint">No stock movements yet.</p>}
        {rows?.length > 0 && (
          <table className="movements">
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
              {rows.map((row) => {
                const when = new Date(row.created_at)
                return (
                  <tr key={row.id}>
                    <td className="nowrap" title={when.toLocaleString()}>
                      {when.toLocaleDateString()}
                      <small>{when.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                    </td>
                    <td>
                      <a href={`#/inventory/item/${row.item_id}`}>{row.item_name}</a>
                      <small>ID {row.item_id}</small>
                    </td>
                    <td>
                      <span className={row.change > 0 ? 'change up' : 'change down'}>
                        {row.change > 0 ? `+${row.change}` : row.change}
                      </span>
                    </td>
                    <td>
                      <a href={personLink(row.user_id)}>{row.username}</a>
                    </td>
                    <td className="note-cell">{row.note || '—'}</td>
                  </tr>
                )
              })}
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
