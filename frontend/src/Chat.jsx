import { useEffect, useRef, useState } from 'react'

import { api, getToken } from './api.js'

const IDEAS = ['How do I add an item?', "Who can see an item's stock?", 'How do friends and blocking work?']

// Sends the conversation and hands each piece of the answer to onText as it arrives. The server answers with
// lines of `data: {...}` (one JSON object each, a blank line between): {text}, then {done}, or {error}.
async function ask(messages, signal, onText) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ messages }),
    signal,
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail = typeof data?.detail === 'string' ? data.detail : 'The assistant could not answer. Please try again.'
    throw Object.assign(new Error(detail), { status: response.status })
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let finished = false
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() // what is left may be half a line
    for (const part of parts) {
      let event
      try {
        event = JSON.parse(part.replace(/^data: /, ''))
      } catch {
        continue
      }
      if (event.text) onText(event.text)
      if (event.error) throw new Error(event.error)
      if (event.done) finished = true
    }
  }
  if (!finished) throw new Error('The answer was cut off. Please try again.')
}

// The help assistant: a round button at the bottom right that opens a small chat. It only knows how Crate works.
// The conversation lives in this component alone: closing the panel keeps it, reloading the page clears it.
export default function Chat({ onExpired }) {
  const [enabled, setEnabled] = useState(false)
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const abort = useRef(null)
  const end = useRef(null)
  const input = useRef(null)

  useEffect(() => {
    api('/chat/config')
      .then((config) => setEnabled(config.enabled))
      .catch((err) => err.status === 401 && onExpired())
    return () => abort.current?.abort()
  }, [onExpired])

  useEffect(() => {
    end.current?.scrollIntoView({ block: 'end' })
  }, [messages, open])

  useEffect(() => {
    if (!open) return undefined
    input.current?.focus()
    const close = (event) => event.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [open])

  if (!enabled) return null

  async function send(question) {
    const asked = question.trim()
    if (!asked || busy) return
    const history = [...messages, { role: 'user', content: asked }]
    setMessages([...history, { role: 'assistant', content: '' }])
    setText('')
    setError('')
    setBusy(true)
    abort.current = new AbortController()
    const add = (piece) =>
      setMessages((list) => list.map((one, at) => (at === list.length - 1 ? { ...one, content: one.content + piece } : one)))
    try {
      await ask(history, abort.current.signal, add)
    } catch (err) {
      if (err.status === 401) onExpired()
      else if (err.name !== 'AbortError') setError(err.message)
    } finally {
      setBusy(false)
      setMessages((list) => (list.at(-1)?.content === '' ? list.slice(0, -1) : list)) // no empty answer left behind
    }
  }

  function startOver() {
    abort.current?.abort()
    setMessages([])
    setError('')
    setBusy(false)
    input.current?.focus()
  }

  return (
    <>
      {open && (
        <section className="chat-panel" aria-label="Help assistant">
          <header>
            <strong>Crate help</strong>
            <span>
              {messages.length > 0 && (
                <button type="button" className="link" onClick={startOver}>
                  New chat
                </button>
              )}
              <button type="button" className="chat-close" aria-label="Close the help assistant" onClick={() => setOpen(false)}>
                ×
              </button>
            </span>
          </header>
          <div className="chat-log" role="log" aria-live="polite">
            {messages.length === 0 && (
              <div className="chat-hello">
                <p>Hi! Ask me how anything in Crate works. I can't see your items or messages, only explain the app.</p>
                {IDEAS.map((idea) => (
                  <button key={idea} type="button" className="chat-idea" onClick={() => send(idea)}>
                    {idea}
                  </button>
                ))}
              </div>
            )}
            {messages.map((message, at) => (
              <p key={at} className={`chat-message ${message.role}`}>
                {message.content || (busy && '…')}
              </p>
            ))}
            {error && <p className="error">{error}</p>}
            <div ref={end} />
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              send(text)
            }}
          >
            <input
              ref={input}
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Ask about Crate"
              aria-label="Your question"
              maxLength={2000}
            />
            <button type="submit" disabled={busy || !text.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-button"
        aria-label={open ? 'Close the help assistant' : 'Open the help assistant'}
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" strokeLinejoin="round" />
        </svg>
      </button>
    </>
  )
}
