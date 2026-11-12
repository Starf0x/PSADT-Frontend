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
    <form className="card login" onSubmit={submit}>
      <div className="brand big"><img src="/favicon.svg" alt="" /><span>PSADT <b>Frontend</b></span></div>
      <p className="muted small">{t('Build PSAppDeployToolkit packages in your browser')}</p>
      <label>{t('Username')}<input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required autoFocus /></label>
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

const ICONS = {
  packages: 'M12 2 21 7v10l-9 5-9-5V7zM3 7l9 5 9-5M12 12v10',
  users: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8',
  system: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  account: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
}
export const Icon = ({ name }) => <svg className="ico" viewBox="0 0 24 24" aria-hidden="true"><path d={ICONS[name]} /></svg>

function Dashboard({ user, version, onLogout, onLang, onMe }) {
  const [page, setPage] = useState('packages')
  // Admins see a dot on System and a banner when a newer version is out (checked at start and every 30 minutes).
  const [update, setUpdate] = useState(null)
  useEffect(() => {
    if (user.role !== 'admin') return
    const check = () => api('/api/system/update').then(i => setUpdate(i.newer ? i.newest : null)).catch(() => {})
    check(); const timer = setInterval(check, 30 * 60 * 1000)
    return () => clearInterval(timer)
  }, [user.role])
  async function logout() {
    await api('/api/auth/logout', { method: 'POST' }).catch(() => {})
    clearCsrf()
    onLogout()
  }
  const item = (key, label, dot) => (
    <button className={`nav-item ${page === key ? 'current' : ''}`} onClick={() => setPage(key)}><Icon name={key} />{label}{dot && <span className="dot" title={t('Update available')} />}</button>)
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><img src="/favicon.svg" alt="" /><span>PSADT <b>Frontend</b></span></div>
        <nav>
          {item('packages', t('Packages'))}
          {user.role === 'admin' && item('users', t('Users'))}
          {user.role === 'admin' && item('system', t('System'), !!update)}
        </nav>
        <div className="side-foot">
          {item('account', <span className="who">{user.display_name || user.username}<small>{t(user.role)}</small></span>)}
          <button className="nav-item" onClick={logout}><Icon name="logout" />{t('Sign out')}</button>
          <div className="row between"><LangPicker onLang={onLang} /><span className="muted small">v{version}</span></div>
        </div>
      </aside>
      <main>
        {update && page !== 'system' && <div className="banner"><span>{t('Version {v} is available.', { v: update })}</span><button className="secondary" onClick={() => setPage('system')}>{t('See what is new')}</button></div>}
        {page === 'packages' && <Packages readOnly={user.role === 'viewer'} />}
        {page === 'users' && <Users me={user} />}
        {page === 'account' && <Account me={user} onMe={onMe} />}
        {page === 'system' && <System />}
      </main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(undefined)
  const [version, setVersion] = useState('')
  const [, setLangState] = useState(getLang())
  const onLang = l => { setLang(l); setLangState(l) }
  // Each user has their own language, stored on the server; the picker on the login page is only for that page.
  const signedIn = u => { if (u?.language) onLang(u.language); setUser(u) }
  const onUserLang = l => { onLang(l); api('/api/auth/language', { method: 'PUT', body: { language: l } }).catch(() => {}) }

  useEffect(() => {
    api('/api/health').then(h => {
      setVersion(h.version)
      // After an update the browser may still hold the old page: load the new one once.
      if (h.version && h.version !== __APP_VERSION__ && sessionStorage.getItem('reloadedFor') !== h.version) {
        sessionStorage.setItem('reloadedFor', h.version); window.location.reload()
      }
    }).catch(() => {})
    api('/api/auth/me').then(signedIn).catch(() => setUser(null))
  }, [])

  if (user === undefined) return null
  return user
    ? <Dashboard user={user} version={version} onLogout={() => setUser(null)} onLang={onUserLang} onMe={setUser} />
    : <div className="center"><Login onLogin={signedIn} /><LangPicker onLang={onLang} /></div>
}
