import { useEffect, useRef, useState } from 'react'
import { api, text, upload } from './api.js'
import { DETECTION_TYPES, PHASES, STEP_TYPES } from './steps.js'
import { t } from './i18n.js'

const TABS = [['app', 'App info'], ['install', 'Install'], ['uninstall', 'Uninstall'], ['repair', 'Repair'], ['files', 'Files'], ['detection', 'Detection'], ['preview', 'Script'], ['export', 'Export']]

// Fields that hold long text get the full width of the step, so arguments and code stay readable.
// Programs already on every Windows PC (see WINDOWS_EXES in the backend).
const WINDOWS_EXES = ['winget.exe', 'msiexec.exe', 'powershell.exe', 'cmd.exe', 'dism.exe', 'reg.exe', 'regsvr32.exe', 'wusa.exe']
const WIDE = new Set(['args', 'code', 'message', 'key', 'path', 'destination'])

// Arguments field with one-click inserts: {Files} and the full path of every uploaded file.
function ArgsInput({ value, onChange, files }) {
  const ref = useRef(null)
  function insert(text) {
    const el = ref.current
    const v = value ?? ''
    const start = el ? el.selectionStart ?? v.length : v.length
    const end = el ? el.selectionEnd ?? v.length : v.length
    const before = v.slice(0, start), after = v.slice(end)
    const pad = before && !/\s$/.test(before) ? ' ' : ''
    const next = before + pad + text + after
    onChange(next)
    requestAnimationFrame(() => { if (el) { el.focus(); const pos = (before + pad + text).length; el.setSelectionRange(pos, pos) } })
  }
  return (
    <>
      <input ref={ref} value={value ?? ''} onChange={e => onChange(e.target.value)} />
      <span className="chips">
        <span className="muted small">{t('Insert:')}</span>
        <button type="button" className="chip" onClick={() => insert('{Files}')} title={t("The package's Files folder on the PC")}>{'{Files}'}</button>
        {files.map(f => <button type="button" key={f.name} className="chip" onClick={() => insert(`"{Files}\\${f.name}"`)} title={t('Full path to this file on the PC, in quotes')}>{f.name}</button>)}
      </span>
    </>
  )
}

// Choose an uploaded file, or browse the PC: the chosen file is uploaded and selected right away.
function FilePicker({ value, onChange, files, accept, onUpload }) {
  const pick = useRef(null)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState('')
  async function onPick(e) {
    const f = e.target.files[0]
    e.target.value = ''
    if (!f) return
    setError(''); setProgress(0)
    try { await onUpload(f, setProgress); onChange(f.name) } catch (err) { setError(`${f.name}: ${err.message}`) }
    setProgress(null)
  }
  return (
    <>
      <span className="row picker">
        <select value={value || ''} onChange={e => onChange(e.target.value || null)} disabled={progress !== null}>
          <option value="">{t('(none)')}</option>
          <optgroup label={t('Uploaded files')}>{files.map(f => <option key={f.name}>{f.name}</option>)}</optgroup>
          {accept === '.exe' && <optgroup label={t('Programs on the Windows PC')}>{WINDOWS_EXES.map(x => <option key={x} value={`windows:${x}`}>{x}</option>)}</optgroup>}
          {value && !value.startsWith('windows:') && !files.some(f => f.name === value) && <option>{value}</option>}
        </select>
        <input ref={pick} type="file" accept={accept} hidden onChange={onPick} />
        <button type="button" className="secondary" disabled={!onUpload || progress !== null} onClick={() => pick.current?.click()}>{t('Browse…')}</button>
      </span>
      {progress !== null && <div className="bar"><div style={{ width: `${Math.round(progress * 100)}%` }} /></div>}
      {error && <span className="error small">{error}</span>}
    </>
  )
}

function Field({ name, label, type, value, onChange, files, wide, accept, onUpload }) {
  if (type === 'bool') return <label className="check"><input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />{t(label)}</label>
  let input
  if (Array.isArray(type)) input = <select value={value} onChange={e => onChange(e.target.value)}>{type.map(o => <option key={o}>{o}</option>)}</select>
  else if (type === 'int') input = <input type="number" value={value} onChange={e => onChange(parseInt(e.target.value || '0', 10))} />
  else if (type === 'code') input = <textarea rows={6} className="mono" value={value} onChange={e => onChange(e.target.value)} />
  else if (type === 'file') input = <FilePicker value={value} onChange={onChange} files={files} accept={accept} onUpload={onUpload} />
  else if (name === 'args') input = <ArgsInput value={value} onChange={onChange} files={files} />
  else input = <input value={value ?? ''} onChange={e => onChange(e.target.value)} />
  return <label className={wide ? 'wide' : undefined}>{t(label)}{input}</label>
}

function StepCard({ step, index, count, files, onUpload, onChange, onMove, onRemove, onSnippet }) {
  const def = STEP_TYPES[step.type]
  return (
    <div className="step">
      <div className="step-head">
        <strong>{index + 1}. {t(def.label)}</strong>
        <span>
          <button className="icon" onClick={onSnippet} title={t('Save as snippet')}>☆</button>
          <button className="icon" disabled={index === 0} onClick={() => onMove(-1)} title={t('Move up')}>↑</button>
          <button className="icon" disabled={index === count - 1} onClick={() => onMove(1)} title={t('Move down')}>↓</button>
          <button className="icon danger" onClick={onRemove} title={t('Delete')}>✕</button>
        </span>
      </div>
      <div className="grid">
        {def.fields.map(([key, label, type, accept]) => (
          <Field key={key} name={key} label={label} type={type} value={step[key]} files={files} accept={accept} onUpload={onUpload} wide={WIDE.has(key)} onChange={v => onChange({ ...step, [key]: v })} />
        ))}
        <Field label="Comment" type="text" value={step.comment || ''} onChange={v => onChange({ ...step, comment: v })} />
      </div>
    </div>
  )
}

function PhaseEditor({ phases, files, onUpload, onChange }) {
  const [adding, setAdding] = useState({})
  const [snippets, setSnippets] = useState([])
  const loadSnippets = () => api('/api/snippets').then(setSnippets).catch(() => {})
  useEffect(() => { loadSnippets() }, [])
  const set = (key, steps) => onChange({ ...phases, [key]: steps })
  async function saveSnippet(step) {
    const name = window.prompt(t('Name for this snippet:'), t(STEP_TYPES[step.type].label))
    if (!name) return
    try { await api('/api/snippets', { method: 'POST', body: { name, step } }); loadSnippets() } catch (e) { window.alert(e.message) }
  }
  async function deleteSnippet(id) {
    const s = snippets.find(x => x.id === id)
    if (s && window.confirm(t('Delete snippet "{name}"?', { name: s.name }))) { await api(`/api/snippets/${id}`, { method: 'DELETE' }); loadSnippets() }
  }
  function add(key) {
    const v = adding[key] || 'msi'
    const step = v.startsWith('snippet:')
      ? structuredClone(snippets.find(x => x.id === Number(v.slice(8))).step)
      : { type: v, comment: '', ...STEP_TYPES[v].defaults }
    set(key, [...phases[key], step])
  }
  return PHASES.map(([key, label]) => {
    const steps = phases[key]
    return (
      <section key={key} className="phase">
        <h3>{t(label)}</h3>
        {steps.length === 0 && <p className="muted">{t('No steps.')}</p>}
        {steps.map((s, i) => (
          <StepCard key={i} step={s} index={i} count={steps.length} files={files} onUpload={onUpload}
            onChange={ns => set(key, steps.map((x, j) => j === i ? ns : x))}
            onRemove={() => set(key, steps.filter((_, j) => j !== i))}
            onMove={d => { const a = [...steps]; [a[i], a[i + d]] = [a[i + d], a[i]]; set(key, a) }}
            onSnippet={() => saveSnippet(s)} />
        ))}
        <div className="row">
          <select value={adding[key] || 'msi'} onChange={e => setAdding({ ...adding, [key]: e.target.value })}>
            <optgroup label={t('Steps')}>{Object.entries(STEP_TYPES).map(([k, d]) => <option key={k} value={k}>{t(d.label)}</option>)}</optgroup>
            {snippets.length > 0 && <optgroup label="Snippets">{snippets.map(x => <option key={x.id} value={`snippet:${x.id}`}>★ {x.name}</option>)}</optgroup>}
          </select>
          <button className="secondary" onClick={() => add(key)}>{t('Add step')}</button>
          {(adding[key] || '').startsWith('snippet:') && <button className="link danger" onClick={() => { deleteSnippet(Number(adding[key].slice(8))); setAdding({ ...adding, [key]: 'msi' }) }}>{t('Delete snippet')}</button>}
        </div>
      </section>
    )
  })
}

const list = v => v.split(',').map(s => s.trim()).filter(Boolean)

function AppInfo({ app, onChange }) {
  const f = (key, label, extra = {}) => (
    <label>{t(label)}<input value={app[key] ?? ''} onChange={e => onChange({ ...app, [key]: e.target.value })} {...extra} /></label>)
  return (
    <div className="grid">
      {f('name', 'Name *', { required: true })}{f('vendor', 'Vendor')}{f('version', 'Version')}
      <label>{t('Architecture')}<select value={app.arch} onChange={e => onChange({ ...app, arch: e.target.value })}>
        {['', 'x86', 'x64', 'arm64'].map(a => <option key={a} value={a}>{a || t('(not specified)')}</option>)}</select></label>
      {f('lang', 'Language')}{f('revision', 'Revision')}{f('author', 'Script author')}{f('script_version', 'Script version')}
      {f('log_path', 'Log folder (empty = default from the System page)', { placeholder: '$envWinDir\\Logs\\Software' })}
      <label>{t('Processes to close (comma-separated, without .exe)')}
        <input defaultValue={app.processes_to_close.join(', ')} onBlur={e => onChange({ ...app, processes_to_close: list(e.target.value) })} /></label>
      <label>{t('Success exit codes')}<input defaultValue={app.success_exit_codes.join(', ')} onBlur={e => onChange({ ...app, success_exit_codes: list(e.target.value).map(Number) })} /></label>
      <label>{t('Reboot exit codes')}<input defaultValue={app.reboot_exit_codes.join(', ')} onBlur={e => onChange({ ...app, reboot_exit_codes: list(e.target.value).map(Number) })} /></label>
      <label className="check"><input type="checkbox" checked={app.require_admin} onChange={e => onChange({ ...app, require_admin: e.target.checked })} />{t('Requires administrator rights')}</label>
    </div>
  )
}

function Files({ id, files, reload }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [queue, setQueue] = useState([])  // [{ name, size, progress 0..1, state: 'wait' | 'up' | 'done' | 'error' }]
  const mb = n => (n / 1048576).toFixed(1)
  async function onPick(e) {
    const picked = [...e.target.files]
    e.target.value = ''
    setBusy(true); setError('')
    setQueue(picked.map(f => ({ name: f.name, size: f.size, progress: 0, state: 'wait' })))
    const set = (i, patch) => setQueue(q => q.map((x, j) => j === i ? { ...x, ...patch } : x))
    for (const [i, f] of picked.entries()) {
      set(i, { state: 'up' })
      try {
        await upload(`/api/packages/${id}/files`, f, p => set(i, { progress: p }))
        set(i, { state: 'done', progress: 1 })
      } catch (err) { set(i, { state: 'error' }); setError(`${f.name}: ${err.message}`) }
    }
    setBusy(false); reload()
    setTimeout(() => setQueue(q => q.filter(x => x.state === 'error')), 2500)
  }
  async function remove(name) {
    await api(`/api/packages/${id}/files/${encodeURIComponent(name)}`, { method: 'DELETE' }).catch(e => setError(e.message))
    reload()
  }
  return (
    <section>
      <p className="muted">{t('Files go into the package folder')} <code>Files</code>.</p>
      <input type="file" multiple onChange={onPick} disabled={busy} />
      {queue.length > 0 && <div className="panel uploads">
        {busy && <strong>{t('Uploading…')}</strong>}
        {queue.map((u, i) => (
          <div key={i} className={`upload ${u.state}`}>
            <div className="row between"><span>{u.name}</span>
              <span className="muted small">{u.state === 'done' ? '✓' : u.state === 'error' ? '✕' : `${mb(u.size * u.progress)} / ${mb(u.size)} MB · ${Math.round(u.progress * 100)}%`}</span></div>
            <div className="bar"><div style={{ width: `${Math.round(u.progress * 100)}%` }} /></div>
          </div>))}
      </div>}
      {error && <p className="error">{error}</p>}
      <table><tbody>{files.map(f => (
        <tr key={f.name}><td>{f.name}</td><td>{(f.size / 1048576).toFixed(1)} MB</td>
          <td><button className="link danger" onClick={() => remove(f.name)}>{t('Delete')}</button></td></tr>))}
      </tbody></table>
    </section>
  )
}

function DetectionEditor({ rules, onChange }) {
  const [type, setType] = useState('msi')
  return (
    <section>
      <p className="muted">{t('Intune uses this script to see whether the app is installed. All rules must match.')}</p>
      {rules.length === 0 && <p className="muted">{t('No rules yet.')}</p>}
      {rules.map((r, i) => (
        <div className="step" key={i}>
          <div className="step-head"><strong>{i + 1}. {t(DETECTION_TYPES[r.type].label)}</strong>
            <button className="icon danger" onClick={() => onChange(rules.filter((_, j) => j !== i))} title={t('Delete')}>✕</button></div>
          <div className="grid">{DETECTION_TYPES[r.type].fields.map(([k, label]) => (
            <label key={k}>{t(label)}<input value={r[k] ?? ''} onChange={e => onChange(rules.map((x, j) => j === i ? { ...x, [k]: e.target.value } : x))} /></label>))}
          </div>
        </div>))}
      <div className="row">
        <select value={type} onChange={e => setType(e.target.value)}>{Object.entries(DETECTION_TYPES).map(([k, d]) => <option key={k} value={k}>{t(d.label)}</option>)}</select>
        <button className="secondary" onClick={() => onChange([...rules, { type, ...DETECTION_TYPES[type].defaults }])}>{t('Add rule')}</button>
      </div>
    </section>
  )
}

const RETENTION_NOTE = {
  export: 'Uploaded files are removed from the server right after the download.',
  1: 'Uploaded files are removed from the server after {n} day(s).', 7: 'Uploaded files are removed from the server after {n} day(s).',
  30: 'Uploaded files are removed from the server after {n} day(s).', 90: 'Uploaded files are removed from the server after {n} day(s).',
}

function Checks({ id, onResult }) {
  const [res, setRes] = useState(null)
  const run = () => { setRes(null); api(`/api/packages/${id}/validate`).then(r => { setRes(r); onResult(r) }).catch(e => setRes({ ok: false, items: [{ level: 'error', text: e.message, vars: {} }] })) }
  useEffect(run, [id])
  if (!res) return <p className="muted">{t('Checking the package…')}</p>
  const icon = { error: '✕', warning: '!', ok: '✓' }
  const items = res.items.length ? res.items : [{ level: 'ok', text: 'Everything is set up correctly', vars: {} }]
  return (
    <div className="panel">
      <div className="row between" style={{ margin: 0 }}>
        <strong>{res.ok ? t('Ready to download') : t('Fix these problems before downloading')}</strong>
        <button className="secondary" onClick={run}>{t('Check again')}</button>
      </div>
      <ul className="checks">{items.map((i, k) => <li key={k} className={i.level}><b>{icon[i.level]}</b><span>{t(i.text, i.vars)}</span></li>)}</ul>
      {!res.syntax_checked && <p className="muted small">{t('PowerShell not available on the server')}: {t('the syntax was not checked.')}</p>}
      {RETENTION_NOTE[res.retention] && <p className="muted small">{t(RETENTION_NOTE[res.retention], { n: res.retention })}</p>}
    </div>
  )
}

function Export({ id }) {
  const [detect, setDetect] = useState('')
  const [ok, setOk] = useState(false)
  useEffect(() => { text(`/api/packages/${id}/detection`).then(setDetect).catch(e => setDetect(e.message)) }, [id])
  const cmd = x => `Invoke-AppDeployToolkit.exe -DeploymentType ${x} -DeployMode Silent`
  const dis = ok ? '' : ' disabled'
  return (
    <section>
      <Checks id={id} onResult={r => setOk(r.ok)} />
      <div className="row">
        <a className={'button' + dis} href={`/api/packages/${id}/export/zip`}>{t('Download')} ZIP</a>
        <a className={'button' + dis} href={`/api/packages/${id}/export/intunewin`}>{t('Download')} .intunewin</a>
        <a className="button secondary" href={`/api/packages/${id}/detection?download=1`}>{t('Download detection script')}</a>
      </div>
      <p className="muted small">{t('Building can take a while with large installer files.')}</p>
      <h3>{t('Intune settings')}</h3>
      <table><tbody>
        <tr><td>{t('Install command')}</td><td><code>{cmd('Install')}</code></td></tr>
        <tr><td>{t('Uninstall command')}</td><td><code>{cmd('Uninstall')}</code></td></tr>
        <tr><td>{t('Install behavior')}</td><td>{t('System')}</td></tr>
        <tr><td>{t('Detection')}</td><td>{t('Custom detection script (below)')}</td></tr>
      </tbody></table>
      <pre className="code">{detect}</pre>
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
        <a className="button" href={`/api/packages/${id}/script?download=1`}>{t('Download')} Invoke-AppDeployToolkit.ps1</a>
        <button className="secondary" onClick={runCheck}>{t('Check syntax')}</button>
        {check && !check.busy && (!check.available ? <span className="muted">{t('PowerShell not available on the server')}</span>
          : check.failed ? <span className="warn">{t('Check could not run')}</span>
          : check.errors.length ? <span className="error">{check.errors.length} {t('error(s)')}</span> : <span className="ok">{t('No syntax errors')}</span>)}
      </div>
      {check?.failed && <div className="panel">
        <p style={{ marginTop: 0 }}><strong>{t('The script could not be checked.')}</strong> {t('PowerShell did not start on the server, so nothing was checked. This is a problem with the server, not a mistake in your package. Ask your administrator to look at it; downloading still works.')}</p>
        <details><summary className="muted small">{t('Technical details for the administrator')}</summary><pre className="code">{check.failed}</pre></details>
      </div>}
      {check?.errors?.length > 0 && <div className="panel">
        <p style={{ marginTop: 0 }}><strong>{t('PowerShell found {n} problem(s) in the script.', { n: check.errors.length })}</strong> {t('Usually this comes from a Custom PowerShell step. Fix the step and check again.')}</p>
        <ul className="checks">{check.errors.map((e, i) => { const m = e.match(/^(\d+):(\d+) (.*)$/); return <li key={i} className="error">{m ? t('Line {l}, column {c}: {msg}', { l: m[1], c: m[2], msg: m[3] }) : e}</li> })}</ul>
      </div>}
      {error ? <pre className="error">{error}</pre> : <pre className="code">{script}</pre>}
    </section>
  )
}

export default function Editor({ id, readOnly, onClose }) {
  const [pkg, setPkg] = useState(null)
  const [tab, setTab] = useState('app')
  const [files, setFiles] = useState([])
  const [dirty, setDirty] = useState(false)
  const [msg, setMsg] = useState(null)

  const loadFiles = () => api(`/api/packages/${id}/files`).then(setFiles).catch(() => {})
  const uploadFile = async (f, onProgress) => { await upload(`/api/packages/${id}/files`, f, onProgress); await loadFiles() }
  useEffect(() => { api(`/api/packages/${id}`).then(setPkg); loadFiles() }, [id])

  // Every change is saved automatically a moment after the last edit, so nothing is lost when the
  // page reloads or the server restarts (e.g. during an update). `rev` counts local edits, so a
  // save that finishes while the user kept typing does not mark the newer edits as saved.
  const rev = useRef(0)
  const latest = useRef(null)
  const update = data => { rev.current += 1; latest.current = data; setPkg(p => ({ ...p, data })); setDirty(true); setMsg(null) }
  async function save() {
    if (readOnly || latest.current === null) return true
    const sent = rev.current
    setMsg({ ok: true, text: t('Saving…') })
    try {
      await api(`/api/packages/${id}`, { method: 'PUT', body: latest.current })
      if (rev.current === sent) { setDirty(false); setMsg({ ok: true, text: t('All changes saved') }) }
      return true
    } catch (e) { setMsg({ ok: false, text: e.message }); return false }
  }
  useEffect(() => {
    if (!dirty || readOnly) return
    const timer = setTimeout(save, 1200)
    return () => clearTimeout(timer)
  }, [pkg, dirty])
  useEffect(() => {
    const warn = e => { if (dirty) { e.preventDefault(); e.returnValue = '' } }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  async function switchTab(next) {
    if (dirty && !(await save()) && ['preview', 'export'].includes(next)) return
    setTab(next)
  }
  async function close() {
    if (dirty && !(await save()) && !window.confirm(t('There are unsaved changes. Close anyway?'))) return
    onClose()
  }

  if (!pkg) return null
  const d = pkg.data
  return (
    <section>
      <div className="row between">
        <h2><button className="link" onClick={close}>{t('Packages')}</button> › {d.app.name}</h2>
        <span className="row">
          {msg && <span className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</span>}
          {readOnly ? <span className="muted">{t('Read only')}</span> : <button onClick={save} disabled={!dirty}>{t('Save now')}</button>}
        </span>
      </div>
      <nav className="tabs">{TABS.map(([k, l]) => <button key={k} className={tab === k ? 'active' : ''} onClick={() => switchTab(k)}>{t(l)}</button>)}</nav>
      <fieldset disabled={readOnly} className="plain">
      {tab === 'app' && <AppInfo app={d.app} onChange={app => update({ ...d, app })} />}
      {['install', 'uninstall', 'repair'].includes(tab) && <PhaseEditor key={tab} phases={d[tab]} files={files} onUpload={readOnly ? null : uploadFile} onChange={p => update({ ...d, [tab]: p })} />}
      {tab === 'files' && <Files id={id} files={files} reload={loadFiles} />}
      {tab === 'detection' && <DetectionEditor rules={d.detection || []} onChange={detection => update({ ...d, detection })} />}
      </fieldset>
      {tab === 'preview' && <Preview id={id} />}
      {tab === 'export' && <Export id={id} />}
    </section>
  )
}
