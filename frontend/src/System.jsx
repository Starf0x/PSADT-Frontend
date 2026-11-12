import { useEffect, useState } from 'react'
import { api } from './api.js'
import { getLang, t } from './i18n.js'

const RETENTION = [['forever', 'Keep forever'], ['export', 'Remove right after a download'], ['1', '1 day'], ['7', '7 days'], ['30', '30 days'], ['90', '90 days']]

function Retention() {
  const [value, setValue] = useState(null)
  const [msg, setMsg] = useState(null)
  useEffect(() => { api('/api/system/settings').then(r => setValue(r.upload_retention)).catch(e => setMsg({ ok: false, text: e.message })) }, [])
  async function change(v) {
    setValue(v)
    try {
      const r = await api('/api/system/settings', { method: 'PUT', body: { upload_retention: v } })
      setMsg({ ok: true, text: r.removed ? t('Saved; {n} old file(s) removed', { n: r.removed }) : t('Saved') })
    } catch (e) { setMsg({ ok: false, text: e.message }) }
  }
  if (value === null) return null
  return (
    <div className="panel">
      <h3 style={{ marginTop: 0 }}>{t('Uploaded files')}</h3>
      <p className="muted small">{t('How long installers and other uploads stay on this server. The package itself is kept; only its files are removed.')}</p>
      <div className="row">
        <select value={value} onChange={e => change(e.target.value)}>{RETENTION.map(([k, l]) => <option key={k} value={k}>{t(l)}</option>)}</select>
        {msg && <span className={msg.ok ? 'ok' : 'error'}>{msg.text}</span>}
      </div>
    </div>
  )
}

function ReleaseNotes() {
  const [res, setRes] = useState(null)
  const lang = getLang()
  useEffect(() => { api(`/api/system/release-notes?lang=${lang}`).then(setRes).catch(() => setRes(null)) }, [lang])
  if (!res || res.notes.length === 0) return null
  return (
    <div className="panel">
      <h3 style={{ marginTop: 0 }}>{res.newer ? t('What the update brings') : t('What is new in this version')}</h3>
      {res.notes.map(n => (
        <div key={n.version} className="notes">
          <span className="badge">v{n.version}</span>
          <ul>{n.items.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </div>))}
    </div>
  )
}

function LogPath() {
  const [value, setValue] = useState(null)
  const [def, setDef] = useState('')
  const [msg, setMsg] = useState(null)
  useEffect(() => { api('/api/system/settings').then(r => { setValue(r.log_path); setDef(r.log_path_default) }).catch(e => setMsg({ ok: false, text: e.message })) }, [])
  async function save(e) {
    e.preventDefault()
    try { await api('/api/system/settings', { method: 'PUT', body: { log_path: value } }); setMsg({ ok: true, text: t('Saved') }) } catch (err) { setMsg({ ok: false, text: err.message }) }
  }
  if (value === null) return null
  return (
    <form className="panel" onSubmit={save}>
      <h3 style={{ marginTop: 0 }}>{t('Default log folder')}</h3>
      <p className="muted small">{t('Where PSADT writes its log on the client. Used for every package that does not set its own; empty = the PSADT default ({d}). PSADT variables such as $envWinDir and $envProgramData work.', { d: def })}</p>
      <div className="row">
        <input value={value} placeholder={def} onChange={e => { setValue(e.target.value); setMsg(null) }} maxLength={260} />
        <button>{t('Save')}</button>
        {msg && <span className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</span>}
      </div>
    </form>
  )
}

// Anonymous daily check-in (as in My Audiobook Collection), disclosed here and switchable.
function Usage() {
  const [s, setS] = useState(null)
  useEffect(() => { api('/api/system/settings').then(setS).catch(() => {}) }, [])
  if (!s) return null
  const set = async on => { try { setS(await api('/api/system/settings', { method: 'PUT', body: { usage: on } })) } catch { /* keep as is */ } }
  return (
    <div className="panel">
      <h3 style={{ marginTop: 0 }}>{t('Anonymous usage')}</h3>
      <p className="muted small">{t('Once a day, and right after an update, the app tells its author it is running: the version, where it runs (Docker, LXC or other), how many days it has been running and a random id for this install. Nothing about packages, files or users is ever sent. It helps decide whether to keep developing the app.')}</p>
      <label className="check"><input type="checkbox" checked={s.usage} disabled={s.usage_env_off} onChange={e => set(e.target.checked)} />{t('Send the anonymous daily check-in')}</label>
      {s.usage_env_off && <p className="muted small">{t('Switched off on the server with PSADT_USAGE_OPTOUT=1.')}</p>}
    </div>
  )
}

export default function System() {
  const [info, setInfo] = useState(null)
  const [error, setError] = useState('')
  const [asked, setAsked] = useState(false)

  const [checking, setChecking] = useState(false)
  const checkNow = () => { setChecking(true); api('/api/system/update?refresh=1').then(i => { setInfo(i); setError('') }).catch(e => setError(e.message)).finally(() => setChecking(false)) }
  const load = () => api('/api/system/update').then(i => { setInfo(i); setError('') }).catch(e => setError(e.message))
  useEffect(() => { load() }, [])

  const p = info?.progress
  const running = asked || info?.pending || (p && !p.done)
  // While updating, poll; the app is restarted part way, so failed polls are expected.
  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => api('/api/system/update').then(i => {
      setInfo(i)
      // Finished on the new version: load the new page after a moment.
      if (i.progress?.done && i.progress.ok && i.progress.to?.replace(/^v/, '') === i.current) setTimeout(() => window.location.reload(), 2500)
      if (i.progress?.done && !i.progress.ok) setAsked(false)
    }).catch(() => {}), 2000)
    return () => clearInterval(timer)
  }, [running])

  async function install() {
    if (!window.confirm(t('Update to v{v}? The app restarts and is unavailable for a few minutes.', { v: info.newest }))) return
    try { setInfo({ ...info, progress: await api('/api/system/update', { method: 'POST' }) }); setAsked(true) } catch (e) { setError(e.message) }
  }

  if (!info) return <section><h2>{t('System')}</h2>{error ? <p className="error">{error}</p> : <p className="muted">{t('Loading…')}</p>}</section>
  const last = info.last
  const pct = p ? (p.done ? 100 : Math.max(4, Math.round((p.step / p.of) * 100))) : 0
  return (
    <section>
      <h2>{t('System')}</h2>
      <table><tbody>
        <tr><td>{t('Installed version')}</td><td>v{info.current}</td></tr>
        <tr><td>{t('Newest release')}</td><td>{info.newest ? `v${info.newest}` : '—'} {info.error && <span className="muted">({info.error})</span>} <button className="link small" onClick={checkNow} disabled={checking}>{checking ? t('Checking…') : t('Check now')}</button></td></tr>
        <tr><td>{t('Install type')}</td><td>{t({ lxc: 'LXC container', docker: 'Docker', other: 'Other / development' }[info.install])}</td></tr>
        {last && <tr><td>{t('Last update')}</td><td>{new Date(last.at).toLocaleString()}: {last.ok ? `${last.from} → ${last.to}` : t('failed')}{last.said && ` (${last.said})`}</td></tr>}
      </tbody></table>

      {running && p ? (
        <div className="card">
          <p>{p.done ? (p.ok ? t('Finished: now on {v}. Reload the page.', { v: p.to }) : `${t('Update failed')}: ${p.said}`) : `${t('Step {n} of {of}', { n: p.step, of: p.of })}: ${t(p.doing)}`}</p>
          <div className={`bar big${p.done ? '' : ' busy'}${p.done && !p.ok ? ' failed' : ''}`}><div style={{ width: `${pct}%` }} /></div>
          <p className="muted small" style={{ textAlign: 'right', margin: '.3rem 0 0' }}>{pct}%</p>
          {!p.done && <p className="muted">{t('The app restarts during the update; this page carries on by itself.')}</p>}
        </div>
      ) : info.newer ? (
        info.install === 'lxc'
          ? <p className="row">{t('A newer version is available.')} <button onClick={install}>{t('Install it')}</button></p>
          : info.install === 'docker'
            ? <p>{t('A newer version is available.')} {t('Update the container with')} <code>docker compose pull &amp;&amp; docker compose up -d</code>.</p>
            : <p>{t('A newer version is available.')} {t('Update this install by hand (git pull, then reinstall).')}</p>
      ) : info.newest && <p className="ok">{t('You are on the newest version.')}</p>}
      {p?.done && !running && !p.ok && <p className="error">{t('Last update failed')}: {p.said}</p>}
      <ReleaseNotes />
      {error && <p className="error">{error}</p>}
      <LogPath />
      <Retention />
      <Usage />
    </section>
  )
}
