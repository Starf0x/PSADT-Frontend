import { useEffect, useState } from 'react'
import { api } from './api.js'
import Editor from './Editor.jsx'

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
    if (!window.confirm(`Pakket "${p.name}" en alle bestanden verwijderen?`)) return
    await api(`/api/packages/${p.id}`, { method: 'DELETE' }).catch(e => setError(e.message))
    load()
  }

  if (openId !== null) return <Editor id={openId} readOnly={readOnly} onClose={() => setOpenId(null)} />

  return (
    <section>
      <h2>Pakketten</h2>
      {!readOnly && <form className="row" onSubmit={create}>
        <input placeholder="Naam van de applicatie" value={name} onChange={e => setName(e.target.value)} required maxLength={100} />
        <button>Nieuw pakket</button>
      </form>}
      {error && <p className="error">{error}</p>}
      {list.length === 0 ? <p className="muted">Nog geen pakketten.</p> : (
        <table>
          <thead><tr><th>Naam</th><th>Leverancier</th><th>Versie</th><th>Gewijzigd</th><th /></tr></thead>
          <tbody>{list.map(p => (
            <tr key={p.id}>
              <td><button className="link" onClick={() => setOpenId(p.id)}>{p.name}</button></td>
              <td>{p.vendor}</td><td>{p.version}</td><td>{new Date(p.updated_at).toLocaleString()}</td>
              <td>{!readOnly && <button className="link danger" onClick={() => remove(p)}>Verwijderen</button>}</td>
            </tr>))}
          </tbody>
        </table>
      )}
    </section>
  )
}
