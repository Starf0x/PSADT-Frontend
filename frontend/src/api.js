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
  if (!res.ok) throw new Error(formatError(data.detail) || `Error ${res.status}`)
  if (data.csrf_token) csrf = data.csrf_token
  return data
}

export async function upload(path, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(path, { method: 'POST', body: form, credentials: 'same-origin', headers: { 'X-CSRF-Token': csrf } })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
  return data
}

export async function text(path) {
  const res = await fetch(path, { credentials: 'same-origin' })
  const body = await res.text()
  if (!res.ok) { let d; try { d = JSON.parse(body).detail } catch { d = body } throw new Error(typeof d === 'string' ? d : JSON.stringify(d)) }
  return body
}

export const clearCsrf = () => { csrf = null }

function formatError(detail) {
  if (!Array.isArray(detail)) return detail
  return detail.map(e => `${e.loc.slice(1).join(' › ')}: ${e.msg}`).join('\n')
}
