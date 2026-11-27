// The app's name and mark, at the top left of every page.
export default function Brand({ href }) {
  return (
    <a className="brand" href={href}>
      <img src="/favicon.svg" alt="" width="30" height="30" />
      Crate
    </a>
  )
}
