import { useEffect, useState } from 'react'
import { api } from './api.js'
import Editor from './Editor.jsx'
import { t } from './i18n.js'

export default function Packages({ readOnly }) {
  const [list, setList] = useState([])
  const [openId, setOpenId] = useState(null)
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const load = () => api('/api/packages').then(setList).catch(e => setError(e.message))
  useEffect(() => { if (openId === null) load() }, [openId])

  async function create(e) {
    e.preventDefault()
    try {
      const p = await api('/api/packages', { method: 'POST', body: { name } })
      setName('')
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
      {!readOnly && <form className="row" onSubmit={create}>
        <input placeholder={t('Application name')} value={name} onChange={e => setName(e.target.value)} required maxLength={100} />
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
              <td>{!readOnly && <button className="link danger" onClick={() => remove(p)}>{t('Delete')}</button>}</td>
            </tr>))}
          </tbody>
        </table>
      )}
    </section>
  )
}
