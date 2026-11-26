import { useState } from 'react'

// A list of rows. Clicking one opens its form underneath; one is open at a time.
export function useRows(onSwitch) {
  const [open, setOpen] = useState('')

  return (id) => ({
    id,
    open: open === id,
    onToggle: () => {
      setOpen(open === id ? '' : id)
      onSwitch()
    },
  })
}

export function Row({ id, label, value, open, onToggle, children }) {
  return (
    <li>
      <button type="button" className="setting" aria-expanded={open} aria-controls={`setting-${id}`} onClick={onToggle}>
        <span>{label}</span>
        <span>
          {value} <span aria-hidden="true">{open ? '⌃' : '›'}</span>
        </span>
      </button>
      {open && (
        <div className="setting-body" id={`setting-${id}`}>
          {children}
        </div>
      )}
    </li>
  )
}
