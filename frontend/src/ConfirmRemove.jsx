import { useEffect, useRef } from 'react'

// A pop-up that names what will be deleted. Cancel comes first, so it is what Enter and Esc do.
export default function ConfirmRemove({ items, onConfirm, onCancel }) {
  const dialog = useRef(null)

  useEffect(() => {
    if (!dialog.current.open) dialog.current.showModal()
  }, [])

  function escape(event) {
    event.preventDefault()
    onCancel()
  }

  return (
    <dialog ref={dialog} className="dialog" aria-labelledby="remove-title" onCancel={escape}>
      <h2 id="remove-title">
        Do you really want to remove {items.length === 1 ? 'this item' : `these ${items.length} items`}?
      </h2>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            {item.name} <small>ID {item.id}</small>
          </li>
        ))}
      </ul>
      <p>Pictures and stock history are deleted too. This can't be undone.</p>
      <div className="dialog-actions">
        <button type="button" className="tool" onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className="tool solid-danger" onClick={onConfirm}>
          Yes, remove
        </button>
      </div>
    </dialog>
  )
}
