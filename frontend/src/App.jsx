import { useEffect, useState } from 'react'
import { api, clearCsrf } from './api.js'
import Packages from './Packages.jsx'
import System from './System.jsx'
import { Account, Users } from './Users.jsx'

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
      <label>Username<input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required /></label>
      <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Sign in</button>
    </form>
  )
}

function Dashboard({ user, version, onLogout }) {
  const [page, setPage] = useState('packages')
  async function logout() {
    await api('/api/auth/logout', { method: 'POST' }).catch(() => {})
    clearCsrf()
    onLogout()
  }
  return (
    <div className="layout">
      <header>
        <nav className="row">
          <strong>PSADT Frontend</strong>
          <button className={`link ${page === 'packages' ? 'current' : ''}`} onClick={() => setPage('packages')}>Packages</button>
          {user.role === 'admin' && <button className={`link ${page === 'users' ? 'current' : ''}`} onClick={() => setPage('users')}>Users</button>}
          {user.role === 'admin' && <button className={`link ${page === 'system' ? 'current' : ''}`} onClick={() => setPage('system')}>System</button>}
        </nav>
        <span className="row">
          <button className="link" onClick={() => setPage('account')}>{user.username} ({user.role})</button> ·
          <button className="link" onClick={logout}>Sign out</button>
        </span>
      </header>
      <main>
        {page === 'packages' && <Packages readOnly={user.role === 'viewer'} />}
        {page === 'users' && <Users me={user} />}
        {page === 'account' && <Account />}
        {page === 'system' && <System />}
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
