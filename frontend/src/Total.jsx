// "Total items: 3" with the number in a pill; while searching, how many are showing.
export default function Total({ label, count, showing, children }) {
  return (
    <div className="total">
      <span>{label}:</span>
      <strong>{count}</strong>
      {showing !== undefined && <span className="total-match">Showing {showing}</span>}
      {children && <span className="total-action">{children}</span>}
    </div>
  )
}
