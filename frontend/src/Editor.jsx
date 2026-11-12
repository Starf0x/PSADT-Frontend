import { useEffect, useState } from 'react'
import { api, text, upload } from './api.js'
import { PHASES, STEP_TYPES } from './steps.js'

const TABS = [['app', 'App-info'], ['install', 'Installatie'], ['uninstall', 'Deïnstallatie'], ['repair', 'Reparatie'], ['files', 'Bestanden'], ['preview', 'Script']]

function Field({ label, type, value, onChange, files }) {
  if (type === 'bool') return <label className="check"><input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />{label}</label>
  let input
  if (Array.isArray(type)) input = <select value={value} onChange={e => onChange(e.target.value)}>{type.map(o => <option key={o}>{o}</option>)}</select>
  else if (type === 'int') input = <input type="number" value={value} onChange={e => onChange(parseInt(e.target.value || '0', 10))} />
  else if (type === 'code') input = <textarea rows={6} className="mono" value={value} onChange={e => onChange(e.target.value)} />
  else if (type === 'file') input = (
    <select value={value || ''} onChange={e => onChange(e.target.value || null)}>
      <option value="">(geen)</option>
      {files.map(f => <option key={f.name}>{f.name}</option>)}
      {value && !files.some(f => f.name === value) && <option>{value}</option>}
    </select>)
  else input = <input value={value ?? ''} onChange={e => onChange(e.target.value)} />
  return <label>{label}{input}</label>
}

function StepCard({ step, index, count, files, onChange, onMove, onRemove }) {
  const def = STEP_TYPES[step.type]
  return (
    <div className="step">
      <div className="step-head">
        <strong>{index + 1}. {def.label}</strong>
        <span>
          <button className="icon" disabled={index === 0} onClick={() => onMove(-1)} title="Omhoog">↑</button>
          <button className="icon" disabled={index === count - 1} onClick={() => onMove(1)} title="Omlaag">↓</button>
          <button className="icon danger" onClick={onRemove} title="Verwijderen">✕</button>
        </span>
      </div>
      <div className="grid">
        {def.fields.map(([key, label, type]) => (
          <Field key={key} label={label} type={type} value={step[key]} files={files} onChange={v => onChange({ ...step, [key]: v })} />
        ))}
        <Field label="Commentaar" type="text" value={step.comment || ''} onChange={v => onChange({ ...step, comment: v })} />
      </div>
    </div>
  )
}

function PhaseEditor({ phases, files, onChange }) {
  const [adding, setAdding] = useState({})
  const set = (key, steps) => onChange({ ...phases, [key]: steps })
  return PHASES.map(([key, label]) => {
    const steps = phases[key]
    return (
      <section key={key} className="phase">
        <h3>{label}</h3>
        {steps.length === 0 && <p className="muted">Geen stappen.</p>}
        {steps.map((s, i) => (
          <StepCard key={i} step={s} index={i} count={steps.length} files={files}
            onChange={ns => set(key, steps.map((x, j) => j === i ? ns : x))}
            onRemove={() => set(key, steps.filter((_, j) => j !== i))}
            onMove={d => { const a = [...steps]; [a[i], a[i + d]] = [a[i + d], a[i]]; set(key, a) }} />
        ))}
        <div className="row">
          <select value={adding[key] || 'msi'} onChange={e => setAdding({ ...adding, [key]: e.target.value })}>
            {Object.entries(STEP_TYPES).map(([t, d]) => <option key={t} value={t}>{d.label}</option>)}
          </select>
          <button className="secondary" onClick={() => {
            const t = adding[key] || 'msi'
            set(key, [...steps, { type: t, comment: '', ...STEP_TYPES[t].defaults }])
          }}>Stap toevoegen</button>
        </div>
      </section>
    )
  })
}

const list = v => v.split(',').map(s => s.trim()).filter(Boolean)

function AppInfo({ app, onChange }) {
  const f = (key, label, extra = {}) => (
    <label>{label}<input value={app[key]} onChange={e => onChange({ ...app, [key]: e.target.value })} {...extra} /></label>)
  return (
    <div className="grid">
      {f('name', 'Naam *', { required: true })}{f('vendor', 'Leverancier')}{f('version', 'Versie')}
      <label>Architectuur<select value={app.arch} onChange={e => onChange({ ...app, arch: e.target.value })}>
        {['', 'x86', 'x64', 'arm64'].map(a => <option key={a} value={a}>{a || '(niet opgegeven)'}</option>)}</select></label>
      {f('lang', 'Taal')}{f('revision', 'Revisie')}{f('author', 'Auteur script')}{f('script_version', 'Scriptversie')}
      <label>Processen om te sluiten (komma-gescheiden, zonder .exe)
        <input defaultValue={app.processes_to_close.join(', ')} onBlur={e => onChange({ ...app, processes_to_close: list(e.target.value) })} /></label>
      <label>Succes-exitcodes<input defaultValue={app.success_exit_codes.join(', ')} onBlur={e => onChange({ ...app, success_exit_codes: list(e.target.value).map(Number) })} /></label>
      <label>Herstart-exitcodes<input defaultValue={app.reboot_exit_codes.join(', ')} onBlur={e => onChange({ ...app, reboot_exit_codes: list(e.target.value).map(Number) })} /></label>
      <label className="check"><input type="checkbox" checked={app.require_admin} onChange={e => onChange({ ...app, require_admin: e.target.checked })} />Beheerdersrechten vereist</label>
    </div>
  )
}

function Files({ id, files, reload }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function onPick(e) {
    setBusy(true); setError('')
    for (const f of e.target.files) {
      try { await upload(`/api/packages/${id}/files`, f) } catch (err) { setError(`${f.name}: ${err.message}`) }
    }
    e.target.value = ''
    setBusy(false); reload()
  }
  async function remove(name) {
    await api(`/api/packages/${id}/files/${encodeURIComponent(name)}`, { method: 'DELETE' }).catch(e => setError(e.message))
    reload()
  }
  return (
    <section>
      <p className="muted">Bestanden komen in de map <code>Files</code> van het pakket.</p>
      <input type="file" multiple onChange={onPick} disabled={busy} />
      {busy && <p>Bezig met uploaden…</p>}
      {error && <p className="error">{error}</p>}
      <table><tbody>{files.map(f => (
        <tr key={f.name}><td>{f.name}</td><td>{(f.size / 1048576).toFixed(1)} MB</td>
          <td><button className="link danger" onClick={() => remove(f.name)}>Verwijderen</button></td></tr>))}
      </tbody></table>
    </section>
  )
}

function Preview({ id }) {
  const [script, setScript] = useState('')
  const [check, setCheck] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { text(`/api/packages/${id}/script`).then(setScript).catch(e => setError(e.message)) }, [id])
  async function runCheck() {
    setCheck({ busy: true })
    try { setCheck(await api(`/api/packages/${id}/check`, { method: 'POST' })) } catch (e) { setCheck({ available: true, errors: [e.message] }) }
  }
  return (
    <section>
      <div className="row">
        <a className="button" href={`/api/packages/${id}/script?download=1`}>Download Invoke-AppDeployToolkit.ps1</a>
        <button className="secondary" onClick={runCheck}>Syntax controleren</button>
        {check && !check.busy && (!check.available ? <span className="muted">PowerShell niet beschikbaar op de server</span>
          : check.errors.length ? <span className="error">{check.errors.length} fout(en)</span> : <span className="ok">Geen syntaxfouten</span>)}
      </div>
      {check?.errors?.length > 0 && <pre className="error">{check.errors.join('\n')}</pre>}
      {error ? <pre className="error">{error}</pre> : <pre className="code">{script}</pre>}
    </section>
  )
}

export default function Editor({ id, onClose }) {
  const [pkg, setPkg] = useState(null)
  const [tab, setTab] = useState('app')
  const [files, setFiles] = useState([])
  const [dirty, setDirty] = useState(false)
  const [msg, setMsg] = useState(null)

  const loadFiles = () => api(`/api/packages/${id}/files`).then(setFiles).catch(() => {})
  useEffect(() => { api(`/api/packages/${id}`).then(setPkg); loadFiles() }, [id])

  const update = data => { setPkg({ ...pkg, data }); setDirty(true); setMsg(null) }
  async function save() {
    try {
      setPkg(await api(`/api/packages/${id}`, { method: 'PUT', body: pkg.data }))
      setDirty(false); setMsg({ ok: true, text: 'Opgeslagen' })
      return true
    } catch (e) { setMsg({ ok: false, text: e.message }); return false }
  }
  async function switchTab(t) {
    if (t === 'preview' && dirty && !(await save())) return
    setTab(t)
  }
  function close() {
    if (dirty && !window.confirm('Er zijn niet-opgeslagen wijzigingen. Toch sluiten?')) return
    onClose()
  }

  if (!pkg) return null
  const d = pkg.data
  return (
    <section>
      <div className="row between">
        <h2><button className="link" onClick={close}>Pakketten</button> › {d.app.name}</h2>
        <span className="row">
          {msg && <span className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</span>}
          <button onClick={save} disabled={!dirty}>Opslaan</button>
        </span>
      </div>
      <nav className="tabs">{TABS.map(([k, l]) => <button key={k} className={tab === k ? 'active' : ''} onClick={() => switchTab(k)}>{l}</button>)}</nav>
      {tab === 'app' && <AppInfo app={d.app} onChange={app => update({ ...d, app })} />}
      {['install', 'uninstall', 'repair'].includes(tab) && <PhaseEditor key={tab} phases={d[tab]} files={files} onChange={p => update({ ...d, [tab]: p })} />}
      {tab === 'files' && <Files id={id} files={files} reload={loadFiles} />}
      {tab === 'preview' && <Preview id={id} />}
    </section>
  )
}
