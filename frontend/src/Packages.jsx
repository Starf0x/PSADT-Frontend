import { Fragment, useEffect, useState } from 'react'
import { api } from './api.js'
import Editor from './Editor.jsx'
import { t } from './i18n.js'

// What a template does: per action the steps, with the file and the command line (install/uninstall string).
const ACTIONS = [['install', 'Install'], ['uninstall', 'Uninstall'], ['repair', 'Repair']]
function stepLine(x) {
  if (x.type === 'msi') return `MSI ${x.action}: ${x.file || x.product_code || ''} ${x.transforms ? `TRANSFORMS=${x.transforms} ` : ''}${x.args || ''}`
  if (x.type === 'exe') return `EXE: ${(x.file || '').replace(/^windows:/, '')} ${x.args || ''}`
  if (x.type === 'uninstall_app') return `${t('Uninstall application by name')}: ${x.name} ${x.args || ''}`
  if (x.type === 'custom') return `PowerShell: ${(x.code || '').split('\n')[0]}`
  return null
}
function TemplateDetails({ id }) {
  const [data, setData] = useState(null)
  useEffect(() => { api(`/api/templates/${id}`).then(r => setData(r.data)).catch(() => setData({})) }, [id])
  if (!data) return <p className="muted small">{t('Loading…')}</p>
  return (
    <div className="tpl-details">
      {ACTIONS.map(([a, label]) => {
        const lines = ['pre', 'main', 'post'].flatMap(p => data[a]?.[p] || []).map(stepLine).filter(Boolean)
        return <div key={a}><b>{t(label)}</b>{lines.length === 0 ? <span className="muted small"> {t('(none)')}</span>
          : <ul>{lines.map((l, i) => <li key={i}><code>{l.trim()}</code></li>)}</ul>}</div>
      })}
      {(data.detection || []).length > 0 && <div><b>{t('Detection')}</b><ul>{data.detection.map((r, i) =>
        <li key={i}><code>{r.type}: {r.product_code || r.path || r.key || r.name}</code></li>)}</ul></div>}
    </div>
  )
}

// Saved package configurations to start new packages from.
function Templates({ list, readOnly, onUse, reload, onError }) {
  const [open, setOpen] = useState(null)
  async function edit(tp) {
    const name = window.prompt(t('Name for this template:'), tp.name)
    if (!name) return
    const description = window.prompt(t('Description (optional):'), tp.description) ?? tp.description
    await api(`/api/templates/${tp.id}`, { method: 'PUT', body: { name, description } }).catch(e => onError(e.message))
    reload()
  }
  async function remove(tp) {
    if (!window.confirm(t('Delete template "{name}"? Packages made from it stay.', { name: tp.name }))) return
    await api(`/api/templates/${tp.id}`, { method: 'DELETE' }).catch(e => onError(e.message))
    reload()
  }
  return (
    <>
      <h3>{t('Templates')}</h3>
      {list.length === 0 ? <p className="muted">{t('No templates yet. Open a package and choose "Save as template".')}</p> : (
        <table>
          <thead><tr><th>{t('Name')}</th><th>{t('Description')}</th><th>{t('Application')}</th><th>{t('Steps')}</th><th>{t('Modified')}</th><th /></tr></thead>
          <tbody>{list.map(tp => (<Fragment key={tp.id}>
            <tr>
              <td><button className="link" onClick={() => setOpen(open === tp.id ? null : tp.id)} title={t('Show the steps and command lines')}>{open === tp.id ? '▾' : '▸'} <b>{tp.name}</b></button></td><td className="muted">{tp.description}</td>
              <td>{[tp.vendor, tp.app].filter(Boolean).join(' ')}</td><td>{tp.steps}</td>
              <td>{new Date(tp.updated_at).toLocaleString()}</td>
              <td className="nowrap">{!readOnly && <>
                <button className="link" onClick={() => onUse(tp)}>{t('Use')}</button>{' '}
                <button className="link" onClick={() => edit(tp)}>{t('Rename')}</button>{' '}
                <button className="link danger" onClick={() => remove(tp)}>{t('Delete')}</button></>}</td>
            </tr>
            {open === tp.id && <tr><td colSpan={6}><TemplateDetails id={tp.id} /></td></tr>}
          </Fragment>))}
          </tbody>
        </table>
      )}
    </>
  )
}

// Counters of successful exports: in total, by you, and per user.
function Stats({ stats }) {
  if (!stats) return null
  return (
    <div className="stats">
      <div className="stat"><span>{t('Packages exported')}</span><b>{stats.total}</b></div>
      <div className="stat"><span>{t('Exported by you')}</span><b>{stats.mine}</b></div>
      <div className="stat wide">
        <span>{t('Per user')}</span>
        {stats.per_user.length === 0 ? <em className="muted small">{t('No exports yet.')}</em> : (
          <ul>{stats.per_user.map((u, i) => (
            <li key={i} className={u.me ? 'me' : undefined}><span>{u.name || t('(removed user)')}</span><b>{u.count}</b></li>))}</ul>)}
      </div>
    </div>
  )
}

export default function Packages({ readOnly, canDelete }) {
  const [stats, setStats] = useState(null)
  const [list, setList] = useState([])
  const [openId, setOpenId] = useState(null)
  const [name, setName] = useState('')
  const [templates, setTemplates] = useState([])
  const [templateId, setTemplateId] = useState('')
  const [error, setError] = useState('')

  const load = () => api('/api/packages').then(setList).catch(e => setError(e.message))
  const loadTemplates = () => api('/api/templates').then(setTemplates).catch(() => {})
  useEffect(() => { if (openId === null) { load(); loadTemplates(); api('/api/stats').then(setStats).catch(() => {}) } }, [openId])

  // With a template the name is optional: empty means the template's application name.
  async function create(e, tid = templateId) {
    e?.preventDefault()
    try {
      const p = await api('/api/packages', { method: 'POST', body: { name, template_id: tid ? Number(tid) : null } })
      setName(''); setTemplateId('')
      setOpenId(p.id)
    } catch (err) { setError(err.message) }
  }

  async function remove(p) {
    if (!window.confirm(t('Delete package "{name}" and all its files?', { name: p.name }))) return
    await api(`/api/packages/${p.id}`, { method: 'DELETE' }).catch(e => setError(e.message))
    load()
  }

  const chosen = templates.find(tp => String(tp.id) === templateId)

  if (openId !== null) return <Editor id={openId} readOnly={readOnly} onClose={() => setOpenId(null)} />

  return (
    <section>
      <h2>{t('Packages')}</h2>
      <Stats stats={stats} />
      {!readOnly && <form className="row" onSubmit={create}>
        <input placeholder={chosen ? t('Name (empty = {name})', { name: chosen.app || chosen.name }) : t('Application name')} value={name} onChange={e => setName(e.target.value)} required={!chosen} maxLength={100} />
        {templates.length > 0 && <select value={templateId} onChange={e => setTemplateId(e.target.value)} aria-label={t('Start from')}>
          <option value="">{t('Empty package')}</option>
          {templates.map(tp => <option key={tp.id} value={tp.id}>{t('Template: {name}', { name: tp.name })}</option>)}
        </select>}
        <button>{t('New package')}</button>
      </form>}
      {error && <p className="error">{error}</p>}
      {list.length === 0 ? <p className="muted">{t('No packages yet.')}</p> : (
        <table>
          <thead><tr><th>{t('Name')}</th><th>{t('Vendor')}</th><th>{t('Version')}</th><th>{t('Modified')}</th><th /></tr></thead>
          <tbody>{list.map(p => (
            <tr key={p.id}>
              <td><button className="link" onClick={() => setOpenId(p.id)}>{p.name}</button></td>
              <td>{p.vendor}</td><td>{p.version}</td><td>{new Date(p.updated_at).toLocaleString()}</td>
              <td>{canDelete && <button className="link danger" onClick={() => remove(p)}>{t('Delete')}</button>}</td>
            </tr>))}
          </tbody>
        </table>
      )}
      <Templates list={templates} readOnly={readOnly} reload={loadTemplates} onError={setError}
        onUse={tp => create(null, String(tp.id))} />
    </section>
  )
}
