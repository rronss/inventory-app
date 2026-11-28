import Brand from './Brand.jsx'
import Hero from './Hero.jsx'
import Login from './Login.jsx'
import Register from './Register.jsx'

// The top bar of the signed-out site has only these two. The homepage is reached through the Crate name, top left.
const TABS = [
  ['signin', 'Sign in'],
  ['register', 'Register'],
]
const PAGES = ['', 'signin', 'register']
// The signed-out site: a bar on top, and the chosen page below it.
export default function Landing({ page, onSignedIn }) {
  const active = PAGES.includes(page) ? page : ''

  return (
    <>
      <header className="topbar">
        <Brand href="#/" />
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
