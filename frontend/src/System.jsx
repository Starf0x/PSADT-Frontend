import { useEffect, useState } from 'react'
import { api } from './api.js'

export default function System() {
  const [info, setInfo] = useState(null)
  const [error, setError] = useState('')
  const [asked, setAsked] = useState(false)

  const load = () => api('/api/system/update').then(i => { setInfo(i); setError('') }).catch(e => setError(e.message))
  useEffect(() => { load() }, [])

  const p = info?.progress
  const running = asked || info?.pending || (p && !p.done)
  // While updating, poll; the app is restarted part way, so failed polls are expected.
  useEffect(() => {
    if (!running) return
    const t = setInterval(() => api('/api/system/update').then(i => {
      setInfo(i)
      if (i.progress?.done && i.progress.to?.replace(/^v/, '') === i.current) setAsked(false)
      if (i.progress?.done && !i.progress.ok) setAsked(false)
    }).catch(() => {}), 2000)
    return () => clearInterval(t)
  }, [running])

  async function install() {
    if (!window.confirm(`Update to v${info.newest}? The app restarts and is unavailable for a few minutes.`)) return
    try { setInfo({ ...info, progress: await api('/api/system/update', { method: 'POST' }) }); setAsked(true) } catch (e) { setError(e.message) }
  }

  if (!info) return <section><h2>System</h2>{error ? <p className="error">{error}</p> : <p className="muted">Loading…</p>}</section>
  const last = info.last
  return (
    <section>
      <h2>System</h2>
      <table><tbody>
        <tr><td>Installed version</td><td>v{info.current}</td></tr>
        <tr><td>Newest release</td><td>{info.newest ? `v${info.newest}` : '—'} {info.error && <span className="muted">({info.error})</span>}</td></tr>
        <tr><td>Install type</td><td>{{ lxc: 'LXC container', docker: 'Docker', other: 'Other / development' }[info.install]}</td></tr>
        {last && <tr><td>Last update</td><td>{new Date(last.at).toLocaleString()}: {last.ok ? `${last.from} → ${last.to}` : 'failed'}{last.said && ` (${last.said})`}</td></tr>}
      </tbody></table>

      {running && p ? (
        <div className="card">
          <p>{p.done ? (p.ok ? `Finished: now on ${p.to}. Reload the page.` : `Update failed: ${p.said}`) : `Step ${p.step} of ${p.of}: ${p.doing}`}</p>
          <progress max={p.of} value={p.step} style={{ width: '100%' }} />
          {!p.done && <p className="muted">The app restarts during the update; this page carries on by itself.</p>}
        </div>
      ) : info.newer ? (
        info.install === 'lxc'
          ? <p className="row">A newer version is available. <button onClick={install}>Install it</button></p>
          : info.install === 'docker'
            ? <p>A newer version is available. Update the container with <code>docker compose pull &amp;&amp; docker compose up -d</code>.</p>
            : <p>A newer version is available. Update this install by hand (git pull, then reinstall).</p>
      ) : info.newest && <p className="ok">You are on the newest version.</p>}
      {p?.done && !running && !p.ok && <p className="error">Last update failed: {p.said}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
