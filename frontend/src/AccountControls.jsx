import { useCallback, useEffect, useState } from 'react'

import { api } from './api.js'

const SWITCHES = [
  ['can_add_items', 'Add items'],
  ['can_move_stock', 'Stock in and out'],
  ['can_edit_items', 'Edit items and their pictures'],
]
const ACTIONS = {
  sign_in: 'Signed in',
  sign_in_failed: 'Wrong password at sign-in',
  account_created: 'Account created',
  created_account: 'Created an account',
  stock_in: 'Stock in',
  stock_out: 'Stock out',
  item_added: 'Added an item',
  item_edited: 'Edited an item',
  item_removed: 'Removed an item',
  image_added: 'Added a picture',
  image_removed: 'Removed a picture',
  profile_changed: 'Changed profile',
  password_changed: 'Changed password',
  email_changed: 'Changed email',
  permissions_changed: 'Permissions changed',
  changed_permissions: 'Changed permissions',
}
const PAGE = 20

// For admins, on someone else's record: what they may do, and what they have done.
export default function AccountControls({ id, handle, onRole }) {
  const [account, setAccount] = useState(null)
  const [role, setRole] = useState('staff')
  const [saved, setSaved] = useState(false)
  const [entries, setEntries] = useState(null)
  const [more, setMore] = useState(false)

  const loadLog = useCallback(
    async (before) => {
      try {
        const page = await api(`/users/${id}/activity?limit=${PAGE}${before ? `&before=${before}` : ''}`)
        setEntries((shown) => (before ? [...shown, ...page] : page))
        setMore(page.length === PAGE)
      } catch (err) {
        handle(err)
      }
    },
    [id, handle],
  )

  useEffect(() => {
    api(`/users/${id}`)
      .then((found) => {
        setAccount(found)
        setRole(found.role)
      })
      .catch(handle)
    loadLog()
  }, [id, handle, loadLog])

  async function save(event) {
    event.preventDefault()
    const form = new FormData(event.target)
    // the switches of an admin are not sent: they have no effect and are kept as they were
    const switches = role === 'admin' ? {} : Object.fromEntries(SWITCHES.map(([field]) => [field, form.has(field)]))
    try {
      const updated = await api(`/users/${id}/permissions`, { method: 'PATCH', body: { role, ...switches } })
      setAccount(updated)
      setSaved(true)
      onRole(updated.role)
      loadLog()
    } catch (err) {
      handle(err)
    }
  }

  return (
    <>
      {account && (
        <form className="card panel permissions" onSubmit={save} onChange={() => setSaved(false)}>
          <h3>Permissions</h3>
          <label>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="staff">Staff</option>
              <option value="admin">Admin: may do everything</option>
            </select>
          </label>
          {SWITCHES.map(([field, label]) => (
            <label key={`${field}-${role === 'admin'}`} className="check">
              <input type="checkbox" name={field} defaultChecked={role === 'admin' || account[field]} disabled={role === 'admin'} />
              {label}
            </label>
          ))}
          <button type="submit">Save permissions</button>
          {saved && <p className="ok">Permissions saved</p>}
        </form>
      )}

      <section className="card panel">
        <h3>Activity log</h3>
        {entries?.length === 0 && <p className="hint">Nothing recorded yet.</p>}
        {entries?.length > 0 && (
          <table className="history">
            <thead>
              <tr>
                <th>Date</th>
                <th>Action</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.created_at).toLocaleString()}</td>
                  <td>{ACTIONS[entry.action] || entry.action}</td>
                  <td>{entry.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {more && (
          <p>
            <button type="button" className="secondary" onClick={() => loadLog(entries[entries.length - 1].id)}>
              Show older
            </button>
          </p>
        )}
      </section>
    </>
  )
}
