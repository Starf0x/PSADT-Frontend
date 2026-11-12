import { useEffect, useState } from 'react'
import { api } from './api.js'
import { t } from './i18n.js'

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
    const timer = setInterval(() => api('/api/system/update').then(i => {
      setInfo(i)
      if (i.progress?.done && i.progress.to?.replace(/^v/, '') === i.current) setAsked(false)
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
  return (
    <section>
      <h2>{t('System')}</h2>
      <table><tbody>
        <tr><td>{t('Installed version')}</td><td>v{info.current}</td></tr>
        <tr><td>{t('Newest release')}</td><td>{info.newest ? `v${info.newest}` : '—'} {info.error && <span className="muted">({info.error})</span>}</td></tr>
        <tr><td>{t('Install type')}</td><td>{t({ lxc: 'LXC container', docker: 'Docker', other: 'Other / development' }[info.install])}</td></tr>
        {last && <tr><td>{t('Last update')}</td><td>{new Date(last.at).toLocaleString()}: {last.ok ? `${last.from} → ${last.to}` : t('failed')}{last.said && ` (${last.said})`}</td></tr>}
      </tbody></table>

      {running && p ? (
        <div className="card">
          <p>{p.done ? (p.ok ? t('Finished: now on {v}. Reload the page.', { v: p.to }) : `${t('Update failed')}: ${p.said}`) : `${t('Step {n} of {of}', { n: p.step, of: p.of })}: ${t(p.doing)}`}</p>
          <progress max={p.of} value={p.step} style={{ width: '100%' }} />
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
      {error && <p className="error">{error}</p>}
      <LogPath />
      <Retention />
    </section>
  )
}
