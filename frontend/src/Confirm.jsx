import { useEffect, useRef } from 'react'

// A pop-up that asks before something is done, naming what it will be done to.
// Cancel comes first, so it is what Enter and Esc do.
export default function Confirm({ title, names, note, yes, onConfirm, onCancel }) {
  const dialog = useRef(null)

  useEffect(() => {
    if (!dialog.current.open) dialog.current.showModal()
  }, [])

  function escape(event) {
    event.preventDefault()
    onCancel()
  }

  return (
    <dialog ref={dialog} className="dialog" aria-labelledby="confirm-title" onCancel={escape}>
      <h2 id="confirm-title">{title}</h2>
      <ul>
        {names.map(([key, name, extra]) => (
          <li key={key}>
            {name} {extra && <small>{extra}</small>}
          </li>
        ))}
      </ul>
      <p>{note}</p>
      <div className="dialog-actions">
        <button type="button" className="tool" onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className="tool solid-danger" onClick={onConfirm}>
          {yes}
        </button>
      </div>
    </dialog>
  )
}
