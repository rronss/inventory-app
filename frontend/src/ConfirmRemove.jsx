import Confirm from './Confirm.jsx'

export default function ConfirmRemove({ items, onConfirm, onCancel }) {
  return (
    <Confirm
      title={`Do you really want to remove ${items.length === 1 ? 'this item' : `these ${items.length} items`}?`}
      names={items.map((item) => [item.id, item.name, `ID ${item.id}`])}
      note="Pictures and stock history are deleted too. This can't be undone."
      yes="Yes, remove"
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  )
}
