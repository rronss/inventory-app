import { Row, useRows } from './SettingRows.jsx'
import { usernameRule } from './username.js'

const field = (form, name) => new FormData(form).get(name)

export default function SecuritySettings({ user, save, notice, onSwitch }) {
  const row = useRows(onSwitch)

  function changePassword(event) {
    event.preventDefault()
    const form = event.target
    const body = { current_password: field(form, 'current'), new_password: field(form, 'next') }
    save(form, '/auth/password', 'POST', body, 'Password changed')
  }

  function changeEmail(event) {
    event.preventDefault()
    const form = event.target
    const body = { new_email: field(form, 'email'), current_password: field(form, 'current') }
    save(form, '/auth/email', 'POST', body, 'Email changed')
  }

  function changeUsername(event) {
    event.preventDefault()
    const form = event.target
    save(form, '/auth/me', 'PATCH', { name: user.name, username: field(form, 'username') }, 'Username saved')
  }

  return (
    <>
      <section className="card narrow">
        <ul className="settings">
          <Row label="Password" value="" {...row('password')}>
            {notice}
            <form onSubmit={changePassword}>
              <input name="current" type="password" autoComplete="current-password" placeholder="Current password" aria-label="Current password" required />
              <input name="next" type="password" autoComplete="new-password" placeholder="New password (8+)" aria-label="New password" minLength="8" required />
              <button type="submit">Change password</button>
            </form>
          </Row>
          <Row label="Email" value="Hidden" {...row('email')}>
            {notice}
            <p className="hint">Your email signs you in. It is never shown, so type the new one in full.</p>
            <form onSubmit={changeEmail}>
              <input name="email" type="email" autoComplete="email" placeholder="New email" aria-label="New email" required />
              <input name="current" type="password" autoComplete="current-password" placeholder="Current password" aria-label="Current password" required />
              <button type="submit">Change email</button>
            </form>
          </Row>
          <Row label="Username" value={user.username} {...row('username')}>
            {notice}
            <form key={user.username} onSubmit={changeUsername}>
              <input name="username" defaultValue={user.username} placeholder="Username" aria-label="Username" {...usernameRule} />
              <button type="submit">Save username</button>
            </form>
          </Row>
        </ul>
      </section>

      <section className="card narrow">
        <h2>Privacy</h2>
        <ul className="facts">
          <li>Colleagues who are signed in can see your name, username, role, bio and photo.</li>
          <li>They can also see which items you added.</li>
          <li>Your username appears next to every stock change you make.</li>
          <li>Admins can see a log of your sign-ins and the changes you make.</li>
          <li>Your email is only for signing in. It is never shown to anyone.</li>
          <li>Your sign-in ends when you log out, close the tab, or after an hour.</li>
        </ul>
      </section>
    </>
  )
}
