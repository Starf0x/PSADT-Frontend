import { useEffect, useState } from 'react'
import { api, clearCsrf } from './api.js'
import { LANGS, getLang, setLang, t } from './i18n.js'
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
      <label>{t('Username')}<input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required /></label>
      <label>{t('Password')}<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
      {error && <p className="error">{error}</p>}
      <button type="submit">{t('Sign in')}</button>
    </form>
  )
}

function LangPicker({ onLang }) {
  return <select className="lang" value={getLang()} onChange={e => onLang(e.target.value)} aria-label="Language">
    {LANGS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
}

function Dashboard({ user, version, onLogout, onLang }) {
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
          <button className={`link ${page === 'packages' ? 'current' : ''}`} onClick={() => setPage('packages')}>{t('Packages')}</button>
          {user.role === 'admin' && <button className={`link ${page === 'users' ? 'current' : ''}`} onClick={() => setPage('users')}>{t('Users')}</button>}
          {user.role === 'admin' && <button className={`link ${page === 'system' ? 'current' : ''}`} onClick={() => setPage('system')}>{t('System')}</button>}
        </nav>
        <span className="row">
          <button className="link" onClick={() => setPage('account')}>{user.username} ({t(user.role)})</button> ·
          <LangPicker onLang={onLang} /> ·
          <button className="link" onClick={logout}>{t('Sign out')}</button>
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
  const [, setLangState] = useState(getLang())
  const onLang = l => { setLang(l); setLangState(l) }

  useEffect(() => {
    api('/api/health').then(h => setVersion(h.version)).catch(() => {})
    api('/api/auth/me').then(setUser).catch(() => setUser(null))
  }, [])

  if (user === undefined) return null
  return user
    ? <Dashboard user={user} version={version} onLogout={() => setUser(null)} onLang={onLang} />
    : <div className="center"><Login onLogin={setUser} /><LangPicker onLang={onLang} /></div>
}
