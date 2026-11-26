const KEY = 'inventory-token'

// sessionStorage: the sign-in ends when the tab is closed.
export const getToken = () => sessionStorage.getItem(KEY)
export const setToken = (token) => (token ? sessionStorage.setItem(KEY, token) : sessionStorage.removeItem(KEY))

// A File body is sent as it is; `blob` asks for the reply as a file.
export async function api(path, { method = 'GET', body, blob = false } = {}) {
  const headers = {}
  const isFile = body instanceof Blob
  if (body) headers['Content-Type'] = isFile ? body.type : 'application/json'
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`

  const response = await fetch(`/api${path}`, { method, headers, body: isFile ? body : body && JSON.stringify(body) })
  if (blob && response.ok) return response.blob()
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Please check the values and try again'
    throw Object.assign(new Error(detail), { status: response.status })
  }
  return data
}
