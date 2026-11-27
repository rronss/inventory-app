import { useEffect, useRef, useState } from 'react'

// A menu that opens on a click and closes on Esc or a click anywhere else.
export default function useDropdown() {
  const [open, setOpen] = useState(false)
  const box = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const away = (event) => !box.current.contains(event.target) && setOpen(false)
    const escape = (event) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', away)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', away)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  return [open, setOpen, box]
}
