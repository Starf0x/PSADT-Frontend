let csrf = null

export async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (csrf && method !== 'GET') headers['X-CSRF-Token'] = csrf
  const res = await fetch(path, {
    method,
    headers,
    credentials: 'same-origin',
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `Fout ${res.status}`)
  if (data.csrf_token) csrf = data.csrf_token
  return data
}

export const clearCsrf = () => { csrf = null }
