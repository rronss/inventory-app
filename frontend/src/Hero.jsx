import { SOON } from './soon.js'

const FEATURES = [
  ['Know what you have', 'Every item with its quantity, and a clear mark on what needs reordering.'],
  ['See each item', 'Every item has its own page with pictures, a description and its stock.'],
  ['Keep the history', 'Each stock movement is recorded with the person who made it.'],
]

// The homepage: the same for visitors and for signed-in people, apart from the buttons passed in.
export default function Hero({ children }) {
  return (
    <>
      <section className="hero">
        <h1>Your stock, in one place.</h1>
        <p className="lead">A simple way for a team to track its items and quantities.</p>
        <p className="actions">{children}</p>
      </section>
      <section className="features">
        {FEATURES.map(([title, text]) => (
          <article key={title} className="card">
            <h2>{title}</h2>
            <p className="hint">{text}</p>
          </article>
        ))}
        <article className="card soon">
          <h2>{SOON.title}</h2>
          <p className="hint">{SOON.text}</p>
        </article>
      </section>
    </>
  )
}
