export const itemLink = (item) => `#/inventory/item/${item.id}`

// Who holds the item, with the one action this user may take.
export function Owner({ item, user, send }) {
  const mine = item.owner?.id === user.id
  return (
    <>
      <span>{item.owner ? (mine ? 'Me' : item.owner.username) : 'Nobody'}</span>
      {!item.owner && (
        <button className="link" onClick={() => send(`/items/${item.id}/attach`)}>
          Attach to me
        </button>
      )}
      {item.owner && (mine || user.role === 'admin') && (
        <button className="link" onClick={() => send(`/items/${item.id}/detach`)}>
          Detach
        </button>
      )}
    </>
  )
}

export function MoveStock({ item, send, withNote }) {
  function move(direction, event) {
    const form = event.currentTarget.form
    const data = new FormData(form)
    const amount = Number(data.get('amount'))
    const body = { change: direction * amount, note: data.get('note') || '' }
    if (amount > 0) send(`/items/${item.id}/movements`, { body }, form)
  }

  return (
    <form className="inline moves" onSubmit={(e) => e.preventDefault()}>
      <input name="amount" type="number" min="1" placeholder="qty" aria-label={`Amount of ${item.name}`} />
      {withNote && <input name="note" className="note" maxLength="200" placeholder="Note (optional)" aria-label="Note" />}
      <button type="button" onClick={(e) => move(1, e)}>
        In
      </button>
      <button type="button" className="secondary" onClick={(e) => move(-1, e)}>
        Out
      </button>
    </form>
  )
}
