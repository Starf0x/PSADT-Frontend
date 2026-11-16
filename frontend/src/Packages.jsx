import { useEffect, useState } from 'react'
import { api } from './api.js'
import Editor from './Editor.jsx'
import { t } from './i18n.js'

// Saved package configurations to start new packages from.
function Templates({ list, readOnly, onUse, reload, onError }) {
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
          <tbody>{list.map(tp => (
            <tr key={tp.id}>
              <td><b>{tp.name}</b></td><td className="muted">{tp.description}</td>
              <td>{[tp.vendor, tp.app].filter(Boolean).join(' ')}</td><td>{tp.steps}</td>
              <td>{new Date(tp.updated_at).toLocaleString()}</td>
              <td className="nowrap">{!readOnly && <>
                <button className="link" onClick={() => onUse(tp)}>{t('Use')}</button>{' '}
                <button className="link" onClick={() => edit(tp)}>{t('Rename')}</button>{' '}
                <button className="link danger" onClick={() => remove(tp)}>{t('Delete')}</button></>}</td>
            </tr>))}
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

  async function create(e) {
    e.preventDefault()
    try {
      const p = await api('/api/packages', { method: 'POST', body: { name, template_id: templateId ? Number(templateId) : null } })
      setName(''); setTemplateId('')
      setOpenId(p.id)
    } catch (err) { setError(err.message) }
  }

  async function remove(p) {
    if (!window.confirm(t('Delete package "{name}" and all its files?', { name: p.name }))) return
    await api(`/api/packages/${p.id}`, { method: 'DELETE' }).catch(e => setError(e.message))
    load()
  }

  if (openId !== null) return <Editor id={openId} readOnly={readOnly} onClose={() => setOpenId(null)} />

  return (
    <section>
      <h2>{t('Packages')}</h2>
      <Stats stats={stats} />
      {!readOnly && <form className="row" onSubmit={create}>
        <input placeholder={t('Application name')} value={name} onChange={e => setName(e.target.value)} required maxLength={100} />
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
        onUse={tp => { setTemplateId(String(tp.id)); window.scrollTo({ top: 0, behavior: 'smooth' }); document.querySelector('form.row input')?.focus() }} />
    </section>
  )
}
