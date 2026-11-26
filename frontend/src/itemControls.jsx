export const itemLink = (item) => `#/inventory/item/${item.id}`

export function MoveStock({ item, send }) {
  function move(direction, event) {
    const form = event.currentTarget.form
    const data = new FormData(form)
    const amount = Number(data.get('amount'))
    const body = { change: direction * amount, note: data.get('note') }
    if (amount > 0) send(`/items/${item.id}/movements`, { body }, form)
  }

  return (
    <form className="moves" onSubmit={(e) => e.preventDefault()}>
      <div className="moves-inputs">
        <input name="amount" type="number" min="1" placeholder="qty" aria-label={`Amount of ${item.name}`} />
        <input name="note" className="note" maxLength="200" placeholder="Note (optional)" aria-label="Note" />
      </div>
      <div className="moves-buttons">
        <button type="button" className="stock-in" onClick={(e) => move(1, e)}>
          Stock in
        </button>
        <button type="button" className="stock-out" onClick={(e) => move(-1, e)}>
          Stock out
        </button>
      </div>
    </form>
  )
}
