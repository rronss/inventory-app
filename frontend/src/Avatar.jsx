import { useFileUrl } from './itemImage.jsx'

// A person's photo, or the first letter of their username.
export default function Avatar({ user, small }) {
  const url = useFileUrl(user.photo_version ? `/people/${user.id}/photo?v=${user.photo_version}` : '')
  const size = small ? 'avatar small' : 'avatar'

  return url ? (
    <img className={size} src={url} alt={`Photo of ${user.username}`} />
  ) : (
    <span className={size} aria-hidden="true">
      {user.username.charAt(0).toUpperCase()}
    </span>
  )
}
