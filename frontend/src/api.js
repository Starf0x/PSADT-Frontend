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

// Files go up in 5 MB pieces, so a reverse proxy with a body-size limit (Zoraxy, Cloudflare, nginx...)
// never sees a large request. XMLHttpRequest instead of fetch: only XHR reports upload progress. onProgress gets 0..1.
const PIECE = 5 * 1024 * 1024

function sendPiece(url, blob, onSent) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    xhr.withCredentials = true
    if (csrf) xhr.setRequestHeader('X-CSRF-Token', csrf)
    xhr.setRequestHeader('Content-Type', 'application/octet-stream')
    // A proxy or full disk can stop a request without closing the connection; give up after a minute without progress.
    let last = Date.now()
    let stalled = false
    const watch = setInterval(() => { if (Date.now() - last > 60000) { stalled = true; xhr.abort() } }, 5000)
    xhr.upload.onprogress = e => { last = Date.now(); onSent(e.loaded) }
    xhr.upload.onload = () => clearInterval(watch) // all sent; the server may still need time to store it
    xhr.onloadend = () => clearInterval(watch)
    xhr.onabort = () => reject(Object.assign(new Error(stalled ? t('Upload stopped: the server received nothing for a minute. A reverse proxy or tunnel may limit the size, or the server disk may be full.') : t('Upload cancelled')), { retry: false }))
    xhr.onerror = () => reject(Object.assign(new Error(t('Upload failed: connection lost')), { retry: true }))
    xhr.onload = () => {
      let data = {}
      try { data = JSON.parse(xhr.responseText) } catch { /* not JSON */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data)
      else if (xhr.status === 409 && /offset (\d+)/.test(data.detail || '')) reject(Object.assign(new Error('offset'), { expected: Number(/offset (\d+)/.exec(data.detail)[1]) }))
      else if (xhr.status === 413 && !data.detail) reject(new Error(t('Upload refused: the file is too large for the server or a proxy in between.')))
      else reject(Object.assign(new Error(formatError(data.detail) || `${t('Error')} ${xhr.status}`), { retry: xhr.status >= 500 }))
    }
    xhr.send(blob)
  })
}

export async function upload(path, file, onProgress = () => {}) {
  const total = file.size
  const base = `${path}/${encodeURIComponent(file.name)}/chunk?total=${total}&offset=`
  let offset = 0
  let data = {}
  do {
    const piece = file.slice(offset, offset + PIECE)
    for (let attempt = 1; ; attempt++) {
      try {
        data = await sendPiece(base + offset, piece, sent => onProgress(total ? (offset + sent) / total : 0))
        break
      } catch (e) {
        if (e.expected !== undefined) { data = { size: e.expected }; break } // the server already has more; go on from there
        if (!e.retry || attempt >= 3) throw e
        await new Promise(r => setTimeout(r, 2000 * attempt))
      }
    }
    offset = data.size ?? offset + piece.size
  } while (offset < total)
  onProgress(1)
  return data
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
