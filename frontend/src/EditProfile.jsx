import { IMAGE_TYPES, imageProblem } from './itemImage.jsx'
import { Row, useRows } from './SettingRows.jsx'

export default function EditProfile({ user, save, notice, fail, onSwitch }) {
  const row = useRows(onSwitch)

  function saveField(event, field, done) {
    event.preventDefault()
    const value = new FormData(event.target).get(field)
    save(event.target, '/auth/me', 'PATCH', { [field]: value }, done)
  }

  function upload(event) {
    const file = event.target.files[0]
    event.target.value = ''
    if (!file) return
    const problem = imageProblem(file)
    if (problem) fail(problem)
    else save(null, '/auth/photo', 'PUT', file, 'Photo saved')
  }

  return (
    <section className="card narrow">
      <ul className="settings">
        <Row label="Bio" value={user.bio ? 'Added' : 'Not set'} {...row('bio')}>
          {notice}
          <form key={user.bio} onSubmit={(e) => saveField(e, 'bio', 'Bio saved')}>
            <textarea name="bio" defaultValue={user.bio} maxLength="500" rows="4" placeholder="A few words about you" aria-label="Bio" />
            <button type="submit">Save bio</button>
          </form>
        </Row>
        <Row label="Profile photo" value={user.photo_version ? 'Added' : 'Not set'} {...row('photo')}>
          {notice}
          <label>
            {user.photo_version ? 'Choose a new photo' : 'Choose a photo'} (PNG, JPEG or WebP, up to 2 MB)
            <input type="file" accept={IMAGE_TYPES} onChange={upload} />
          </label>
          {user.photo_version > 0 && (
            <button type="button" className="secondary" onClick={() => save(null, '/auth/photo', 'DELETE', undefined, 'Photo removed')}>
              Remove photo
            </button>
          )}
        </Row>
      </ul>
    </section>
  )
}
