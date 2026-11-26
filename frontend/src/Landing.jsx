import Login from './Login.jsx'
import Register from './Register.jsx'

const TABS = [
  ['', 'Home'],
  ['signin', 'Sign in'],
  ['register', 'Register'],
]
const FEATURES = [
  ['Know what you have', 'Every item with its quantity, and a clear mark on what needs reordering.'],
  ['See who holds what', 'Attach items to your profile, so nothing goes missing without a name next to it.'],
  ['Keep the history', 'Each stock movement is recorded with the person who made it.'],
]

// The signed-out site: a bar of tabs on top, and the chosen tab below it.
export default function Landing({ page, onSignedIn }) {
  const active = TABS.some(([key]) => key === page) ? page : ''

  return (
    <>
      <header className="topbar">
        <a className="brand" href="#/">
          Inventory
        </a>
        <nav className="end">
          {TABS.map(([key, label]) => (
            <a key={label} href={`#/${key}`} aria-current={active === key ? 'page' : undefined}>
              {label}
            </a>
          ))}
        </nav>
      </header>

      {active === 'signin' && (
        <div className="form-page">
          <Login onSignedIn={onSignedIn} />
        </div>
      )}
      {active === 'register' && (
        <div className="form-page">
          <Register onSignedIn={onSignedIn} />
        </div>
      )}
      {active === '' && (
        <>
          <section className="hero">
            <h1>Your stock, in one place.</h1>
            <p className="lead">A simple way for a team to track items, quantities and who is responsible for them.</p>
            <p className="actions">
              <a className="button" href="#/register">
                Create an account
              </a>
              <a className="button ghost" href="#/signin">
                Sign in
              </a>
            </p>
          </section>
          <section className="features">
            {FEATURES.map(([title, text]) => (
              <article key={title} className="card">
                <h2>{title}</h2>
                <p className="hint">{text}</p>
              </article>
            ))}
          </section>
        </>
      )}
    </>
  )
}
