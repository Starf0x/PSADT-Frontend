import { useEffect, useState } from 'react'
import { api } from './api.js'
import { t } from './i18n.js'

const ROLES = { admin: 'Administrator', editor: 'Editor', viewer: 'Read only' }

export function Users({ me }) {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({ username: '', password: '', role: 'editor' })
  const [msg, setMsg] = useState(null)
  const load = () => api('/api/users').then(setUsers).catch(e => setMsg({ ok: false, text: e.message }))
  useEffect(() => { load() }, [])

  async function run(fn, ok) {
    try { await fn(); setMsg({ ok: true, text: ok }); load() } catch (e) { setMsg({ ok: false, text: e.message }) }
  }
  const create = e => { e.preventDefault(); run(async () => { await api('/api/users', { method: 'POST', body: form }); setForm({ username: '', password: '', role: 'editor' }) }, t('User created')) }
  const setRole = (u, role) => run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { role } }), t('Role changed'))
  const unlock = u => run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { unlock: true } }), t('Account unlocked'))
  const reset = u => {
    const password = window.prompt(t('New password for {name} (at least 12 characters):', { name: u.username }))
    if (password) run(() => api(`/api/users/${u.id}`, { method: 'PUT', body: { password } }), t('Password changed'))
  }
  const remove = u => window.confirm(t('Delete user {name}?', { name: u.username })) && run(() => api(`/api/users/${u.id}`, { method: 'DELETE' }), t('User deleted'))

  return (
    <section>
      <h2>{t('Users')}</h2>
      <form className="row" onSubmit={create}>
        <input placeholder={t('Username')} value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required minLength={3} autoComplete="off" />
        <input type="password" placeholder={t('Password (min. 12 characters)')} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required minLength={12} autoComplete="new-password" />
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>{Object.entries(ROLES).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}</select>
        <button>{t('Add')}</button>
      </form>
      {msg && <p className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</p>}
      <table>
        <thead><tr><th>{t('User')}</th><th>{t('Role')}</th><th>{t('Status')}</th><th /></tr></thead>
        <tbody>{users.map(u => (
          <tr key={u.id}>
            <td>{u.username}{u.username === me.username && ` (${t('you')})`}</td>
            <td><select value={u.role} onChange={e => setRole(u, e.target.value)}>{Object.entries(ROLES).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}</select></td>
            <td>{u.locked ? <button className="link" onClick={() => unlock(u)}>{t('Locked, unlock')}</button> : t('Active')}</td>
            <td><span className="row">
              <button className="link" onClick={() => reset(u)}>{t('Password')}</button>
              {u.username !== me.username && <button className="link danger" onClick={() => remove(u)}>{t('Delete')}</button>}
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
    if (form.new_password !== form.repeat) return setMsg({ ok: false, text: t('Passwords do not match') })
    try {
      await api('/api/auth/password', { method: 'POST', body: { current_password: form.current_password, new_password: form.new_password } })
      setForm({ current_password: '', new_password: '', repeat: '' })
      setMsg({ ok: true, text: t('Password changed; other sessions were signed out') })
    } catch (err) { setMsg({ ok: false, text: err.message }) }
  }
  const f = (k, label, ac) => <label>{t(label)}<input type="password" value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} required autoComplete={ac} /></label>
  return (
    <form className="card" onSubmit={submit}>
      <h2>{t('Change password')}</h2>
      {f('current_password', 'Current password', 'current-password')}
      {f('new_password', 'New password (min. 12 characters)', 'new-password')}
      {f('repeat', 'Repeat new password', 'new-password')}
      {msg && <p className={msg.ok ? 'ok' : 'error pre'}>{msg.text}</p>}
      <button>{t('Save')}</button>
    </form>
  )
}
