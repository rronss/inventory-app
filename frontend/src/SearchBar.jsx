// A rounded search box with a magnifier.
export default function SearchBar({ value, onChange, placeholder, label }) {
  return (
    <label className="search-bar">
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m15.5 15.5 5 5" />
      </svg>
      <input type="search" placeholder={placeholder} aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  )
}
