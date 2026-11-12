import { t } from './i18n.js'

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
  if (!res.ok) throw new Error(formatError(data.detail) || `${t('Error')} ${res.status}`)
  if (data.csrf_token) csrf = data.csrf_token
  return data
}

// XMLHttpRequest instead of fetch: only XHR reports upload progress. onProgress gets 0..1.
export function upload(path, file, onProgress = () => {}) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', path)
    xhr.withCredentials = true
    if (csrf) xhr.setRequestHeader('X-CSRF-Token', csrf)
    xhr.upload.onprogress = e => { if (e.lengthComputable) onProgress(e.loaded / e.total) }
    xhr.onload = () => {
      let data = {}
      try { data = JSON.parse(xhr.responseText) } catch { /* not JSON */ }
      if (xhr.status >= 200 && xhr.status < 300) { onProgress(1); resolve(data) } else reject(new Error(formatError(data.detail) || `${t('Error')} ${xhr.status}`))
    }
    xhr.onerror = () => reject(new Error(t('Upload failed: connection lost')))
    xhr.send(form)
  })
}

export async function text(path) {
  const res = await fetch(path, { credentials: 'same-origin' })
  const body = await res.text()
  if (!res.ok) { let d; try { d = JSON.parse(body).detail } catch { d = body } throw new Error(typeof d === 'string' ? t(d) : JSON.stringify(d)) }
  return body
}

export const clearCsrf = () => { csrf = null }

function formatError(detail) {
  if (!Array.isArray(detail)) return typeof detail === 'string' ? t(detail) : detail
  return detail.map(e => `${e.loc.slice(1).join(' › ')}: ${e.msg}`).join('\n')
}

// Downloads a built file with feedback: onState('build') while the server builds it, then
// onState('get', 0..1) while it arrives. Saves it under the name the server gives.
export function download(path, onState = () => {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('GET', path)
    xhr.withCredentials = true
    xhr.responseType = 'blob'
    onState('build')
    xhr.onprogress = e => onState('get', e.lengthComputable ? e.loaded / e.total : null)
    xhr.onload = async () => {
      if (xhr.status < 200 || xhr.status >= 300) {
        let detail = null
        try { detail = JSON.parse(await xhr.response.text()).detail } catch { /* not JSON */ }
        return reject(new Error(formatError(detail) || `${t('Error')} ${xhr.status}`))
      }
      const name = /filename="?([^";]+)"?/.exec(xhr.getResponseHeader('Content-Disposition') || '')?.[1] || 'download'
      const a = document.createElement('a')
      a.href = URL.createObjectURL(xhr.response); a.download = name
      document.body.appendChild(a); a.click(); a.remove()
      setTimeout(() => URL.revokeObjectURL(a.href), 60000)
      resolve(name)
    }
    xhr.onerror = () => reject(new Error(t('Download failed: connection lost')))
    xhr.send()
  })
}
