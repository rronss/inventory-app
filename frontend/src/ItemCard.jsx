import { itemLink } from './itemControls.jsx'
import { Picture } from './itemImage.jsx'

function statusOf(item) {
  if (item.quantity === null) return { label: 'Private', tone: 'hidden' }
  if (item.quantity === 0) return { label: 'Out of stock', tone: 'low' }
  if (item.low_stock) return { label: 'Low stock', tone: 'low' }
  return { label: 'In stock', tone: '' }
}

// An item as a card: picture, status, name and how many there are. `children` goes underneath.
export default function ItemCard({ item, children }) {
  const { label, tone } = statusOf(item)

  return (
    <li className="tile">
      <a className="tile-picture" href={itemLink(item)} aria-label={item.name}>
        {item.image_ids.length > 0 ? <Picture itemId={item.id} imageId={item.image_ids[0]} alt="" /> : <span className="hint">No image</span>}
        <span className={`badge ${tone}`}>{label}</span>
      </a>
      <a className="tile-name" href={itemLink(item)}>
        {item.name}
      </a>
      <p className={`tile-count ${tone}`}>
        {item.quantity === null ? (
          'Stock is private'
        ) : (
          <>
            <strong>{item.quantity}</strong> in stock
          </>
        )}
      </p>
      {children}
    </li>
  )
}
