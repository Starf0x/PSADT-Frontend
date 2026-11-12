import { useEffect, useState } from 'react'
import { api, clearCsrf } from './api.js'

function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      onLogin(await api('/api/auth/login', { method: 'POST', body: { username, password } }))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>PSADT Frontend</h1>
      <label>Gebruikersnaam<input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required /></label>
      <label>Wachtwoord<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Inloggen</button>
    </form>
  )
}

function Dashboard({ user, version, onLogout }) {
  async function logout() {
    await api('/api/auth/logout', { method: 'POST' }).catch(() => {})
    clearCsrf()
    onLogout()
  }
  return (
    <div className="layout">
      <header>
        <strong>PSADT Frontend</strong>
        <span>{user.username} · <button className="link" onClick={logout}>Uitloggen</button></span>
      </header>
      <main>
        <h2>Welkom, {user.username}</h2>
        <p>De package-editor volgt in stap 2.</p>
      </main>
      <footer>v{version}</footer>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(undefined)
  const [version, setVersion] = useState('')

  useEffect(() => {
    api('/api/health').then(h => setVersion(h.version)).catch(() => {})
    api('/api/auth/me').then(setUser).catch(() => setUser(null))
  }, [])

  if (user === undefined) return null
  return user
    ? <Dashboard user={user} version={version} onLogout={() => setUser(null)} />
    : <div className="center"><Login onLogin={setUser} /></div>
}
