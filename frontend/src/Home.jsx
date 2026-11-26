import { itemLink } from './itemControls.jsx'
import useItems from './useItems.js'

export default function Home({ user, onExpired }) {
  const { items, error } = useItems('', onExpired)
  const low = items.filter((item) => item.low_stock)

  const stats = [
    ['Items', items.length, '#/inventory'],
    ['Low stock', low.length, '#/inventory'],
  ]

  return (
    <>
      <h1>Welcome, {user.username}</h1>
      {error && <p className="error">{error}</p>}
      <div className="stats">
        {stats.map(([label, value, href]) => (
          <a key={label} className="card stat" href={href}>
            <strong>{value}</strong>
            <span>{label}</span>
          </a>
        ))}
      </div>
      <section className="card">
        <h2>Needs reordering</h2>
        {low.length === 0 && <p className="hint">Nothing is running low.</p>}
        <ul className="list">
          {low.map((item) => (
            <li key={item.id}>
              <span>
                <a href={itemLink(item)}>{item.name}</a> <small>{item.sku}</small>
              </span>
              <span>
                {item.quantity} left, reorder at {item.reorder_level}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
