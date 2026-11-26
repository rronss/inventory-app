import { useEffect, useState } from 'react'

import { api } from './api.js'

export const IMAGE_TYPES = 'image/png,image/jpeg,image/webp'
export const MAX_IMAGES = 5

// The same limits the server applies, checked before anything is sent.
export function imageProblem(file) {
  if (!IMAGE_TYPES.split(',').includes(file.type)) return 'An image must be a PNG, JPEG or WebP file'
  if (file.size > 2 * 1024 * 1024) return 'An image must be 2 MB or smaller'
  return ''
}

export function Picture({ itemId, imageId, alt }) {
  const url = useFileUrl(`/items/${itemId}/images/${imageId}`)
  return url && <img src={url} alt={alt} />
}

// The server wants the sign-in token for these files, so they are fetched and shown from memory.
export function useFileUrl(path) {
  const [url, setUrl] = useState('')

  useEffect(() => {
    if (!path) return undefined
    let wanted = true
    let made = ''
    api(path, { blob: true })
      .then((file) => {
        if (!wanted) return
        made = URL.createObjectURL(file)
        setUrl(made)
      })
      .catch(() => {})
    return () => {
      wanted = false
      if (made) URL.revokeObjectURL(made)
      setUrl('')
    }
  }, [path])

  return url
}

export function Slideshow({ item, shown, onShow }) {
  const ids = item.image_ids
  const several = ids.length > 1
  const step = (by) => onShow((shown + by + ids.length) % ids.length)

  if (ids.length === 0) {
    return (
      <div className="slideshow">
        <div className="product-image empty">
          <span className="hint">No image yet</span>
        </div>
      </div>
    )
  }

  function arrowKeys(event) {
    if (several && event.key === 'ArrowLeft') step(-1)
    if (several && event.key === 'ArrowRight') step(1)
  }

  return (
    <div
      className="slideshow"
      role="region"
      aria-roledescription="carousel"
      aria-label={`Pictures of ${item.name}`}
      tabIndex={0}
      onKeyDown={arrowKeys}
    >
      <div className="product-image">
        <div className="track" style={{ transform: `translateX(-${shown * 100}%)` }}>
          {ids.map((id, index) => (
            <div className="slide" key={id} aria-hidden={index !== shown}>
              <Picture itemId={item.id} imageId={id} alt={`${item.name}, picture ${index + 1} of ${ids.length}`} />
            </div>
          ))}
        </div>
        {several && (
          <>
            <button type="button" className="arrow prev" aria-label="Previous picture" onClick={() => step(-1)}>
              ‹
            </button>
            <button type="button" className="arrow next" aria-label="Next picture" onClick={() => step(1)}>
              ›
            </button>
            <span className="counter">
              {shown + 1} / {ids.length}
            </span>
          </>
        )}
      </div>
      {several && (
        <div className="dots">
          {ids.map((id, index) => (
            <button
              type="button"
              key={id}
              aria-label={`Picture ${index + 1}`}
              aria-current={index === shown}
              onClick={() => onShow(index)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
