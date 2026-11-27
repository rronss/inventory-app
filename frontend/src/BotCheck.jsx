import { useEffect, useRef } from 'react'

const SCRIPT = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
let loading = null

function load() {
  loading ||= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = SCRIPT
    script.onload = resolve
    script.onerror = () => {
      loading = null
      script.remove()
      reject(new Error('The robot check could not be loaded'))
    }
    document.head.appendChild(script)
  })
  return loading
}

// Cloudflare Turnstile. A token can be used once, so the parent remounts this to get a new one.
export default function BotCheck({ siteKey, onToken, onProblem }) {
  const box = useRef(null)

  useEffect(() => {
    let widget = null
    let gone = false
    load()
      .then(() => {
        if (gone) return
        widget = window.turnstile.render(box.current, {
          sitekey: siteKey,
          callback: onToken,
          'expired-callback': () => onToken(''),
        })
      })
      .catch((err) => onProblem(err.message))
    return () => {
      gone = true
      if (widget !== null) window.turnstile.remove(widget)
    }
  }, [siteKey, onToken, onProblem])

  return <div className="bot-check" ref={box} />
}
