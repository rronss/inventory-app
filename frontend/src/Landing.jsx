import Hero from './Hero.jsx'
import Login from './Login.jsx'
import Register from './Register.jsx'

const TABS = [
  ['', 'Home'],
  ['signin', 'Sign in'],
  ['register', 'Register'],
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
        <Hero>
          <a className="button" href="#/register">
            Create an account
          </a>
          <a className="button ghost" href="#/signin">
            Sign in
          </a>
        </Hero>
      )}
    </>
  )
}
