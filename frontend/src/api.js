const KEY = 'inventory-token'

// sessionStorage: the sign-in ends when the tab is closed.
export const getToken = () => sessionStorage.getItem(KEY)
export const setToken = (token) => (token ? sessionStorage.setItem(KEY, token) : sessionStorage.removeItem(KEY))

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`

  const response = await fetch(`/api${path}`, { method, headers, body: body && JSON.stringify(body) })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Please check the values and try again'
    throw Object.assign(new Error(detail), { status: response.status })
  }
  return data
}
