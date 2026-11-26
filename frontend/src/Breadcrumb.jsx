// Items > ID 2 > Edit. The last step is where you are; the ones before it are links.
export default function Breadcrumb({ id, editing }) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <a href="#/inventory">Items</a>
      <span aria-hidden="true">&gt;</span>
      {editing ? <a href={`#/inventory/item/${id}`}>ID {id}</a> : <span aria-current="page">ID {id}</span>}
      {editing && (
        <>
          <span aria-hidden="true">&gt;</span>
          <span aria-current="page">Edit</span>
        </>
      )}
    </nav>
  )
}
