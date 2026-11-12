import { useEffect, useState } from 'react'
import { api } from './api.js'

const ROLES = { admin: 'Beheerder', editor: 'Bewerker', viewer: 'Alleen lezen' }

export function Users({ me }) {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({ username: '', password: '', role: 'editor' })
  const [msg, setMsg] = useState(null)
  const load = () => api('/api/users').then(setUsers).catch(e => setMsg({ ok: false, text: e.message }))
  useEffect(() => { load() }, [])

  async function run(fn, ok) {
    try { await fn(); setMsg({ ok: true, text: ok }); load() } catch (e) { setMsg({ ok: false, text: e.message }) }
  }
  const create = e => { e.preventDefault(); run(async () => { await api('/api/users', { method: 'POST', body: form }); setForm({ username: '', password: '', role: 'editor' }) }, 'Gebruiker aangemaakt') }
  const setRole = (u, role) => run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { role } }), 'Rol aangepast')
  const unlock = u => run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { unlock: true } }), 'Account ontgrendeld')
  const reset = u => {
    const password = window.prompt(`Nieuw wachtwoord voor ${u.username} (minimaal 12 tekens):`)
    if (password) run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { password } }), 'Wachtwoord gewijzigd')
  }
  const remove = u => window.confirm(`Gebruiker ${u.username} verwijderen?`) && run(() => api(`/api/users/${u.id}`, { method: 'DELETE' }), 'Gebruiker verwijderd')

  return (
    <section>
      <h2>Gebruikers</h2>
      <form className="row" onSubmit={create}>
        <input placeholder="Gebruikersnaam" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required minLength={3} autoComplete="off" />
        <input type="password" placeholder="Wachtwoord (min. 12 tekens)" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required minLength={12} autoComplete="new-password" />
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>{Object.entries(ROLES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <button>Toevoegen</button>
      </form>
      {msg && <p className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</p>}
      <table>
        <thead><tr><th>Gebruiker</th><th>Rol</th><th>Status</th><th /></tr></thead>
        <tbody>{users.map(u => (
          <tr key={u.id}>
            <td>{u.username}{u.username === me.username && ' (jij)'}</td>
            <td><select value={u.role} onChange={e => setRole(u, e.target.value)}>{Object.entries(ROLES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></td>
            <td>{u.locked ? <button className="link" onClick={() => unlock(u)}>Geblokkeerd, ontgrendelen</button> : 'Actief'}</td>
            <td><span className="row">
              <button className="link" onClick={() => reset(u)}>Wachtwoord</button>
              {u.username !== me.username && <button className="link danger" onClick={() => remove(u)}>Verwijderen</button>}
            </span></td>
          </tr>))}
        </tbody>
      </table>
    </section>
  )
}

export function Account() {
  const [form, setForm] = useState({ current_password: '', new_password: '', repeat: '' })
  const [msg, setMsg] = useState(null)
  async function submit(e) {
    e.preventDefault()
    if (form.new_password !== form.repeat) return setMsg({ ok: false, text: 'Wachtwoorden komen niet overeen' })
    try {
      await api('/api/auth/password', { method: 'POST', body: { current_password: form.current_password, new_password: form.new_password } })
      setForm({ current_password: '', new_password: '', repeat: '' })
      setMsg({ ok: true, text: 'Wachtwoord gewijzigd; andere sessies zijn uitgelogd' })
    } catch (err) { setMsg({ ok: false, text: err.message }) }
  }
  const f = (k, label, ac) => <label>{label}<input type="password" value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} required autoComplete={ac} /></label>
  return (
    <form className="card" onSubmit={submit}>
      <h2>Wachtwoord wijzigen</h2>
      {f('current_password', 'Huidig wachtwoord', 'current-password')}
      {f('new_password', 'Nieuw wachtwoord (min. 12 tekens)', 'new-password')}
      {f('repeat', 'Herhaal nieuw wachtwoord', 'new-password')}
      {msg && <p className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</p>}
      <button>Opslaan</button>
    </form>
  )
}
