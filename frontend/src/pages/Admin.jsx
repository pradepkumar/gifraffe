import { useState, useEffect } from 'react'
import { adminLogin, getAdminQueue, approveGif, rejectGif } from '../api.js'
import TagChip from '../components/TagChip.jsx'

export default function Admin() {
  const [authed, setAuthed] = useState(false)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState(null)
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionInProgress, setActionInProgress] = useState(null)

  const loadQueue = async () => {
    setLoading(true)
    try {
      const data = await getAdminQueue()
      setQueue(data.results)
    } catch (e) {
      if (e.message === 'Unauthorized') setAuthed(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Try to load queue — if it works, we're already authed (existing session)
    getAdminQueue().then(data => { setAuthed(true); setQueue(data.results) }).catch(() => {})
  }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError(null)
    try {
      await adminLogin(password)
      setAuthed(true)
      loadQueue()
    } catch {
      setLoginError('Incorrect password')
    }
  }

  const handleApprove = async (id) => {
    setActionInProgress(id)
    try {
      await approveGif(id)
      setQueue(q => q.filter(g => g.id !== id))
    } catch (e) {
      alert('Failed to approve — ' + e.message)
    } finally {
      setActionInProgress(null)
    }
  }

  const handleReject = async (id) => {
    if (!confirm('Reject and delete this GIF?')) return
    setActionInProgress(id)
    try {
      await rejectGif(id)
      setQueue(q => q.filter(g => g.id !== id))
    } catch (e) {
      alert('Failed to reject — ' + e.message)
    } finally {
      setActionInProgress(null)
    }
  }

  if (!authed) {
    return (
      <div style={{ maxWidth: 360, margin: '60px auto', padding: 24 }}>
        <h2 style={{ marginBottom: 20, color: '#5a3a10' }}>Admin Login</h2>
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            required
            style={{ padding: '12px', borderRadius: 10, border: '2px solid #e8c97a', fontSize: '1rem', outline: 'none' }}
          />
          {loginError && <p style={{ color: '#c0392b', fontSize: '0.9rem' }}>{loginError}</p>}
          <button type="submit" style={{ background: '#d4880a', color: '#fff', border: 'none', borderRadius: 10, padding: 13, fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}>
            Login
          </button>
        </form>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ color: '#5a3a10' }}>Approval Queue</h2>
        <button onClick={loadQueue} style={{ background: '#f5e6c0', border: 'none', borderRadius: 8, padding: '8px 14px', cursor: 'pointer', fontWeight: 600 }}>
          Refresh
        </button>
      </div>

      {loading && <p style={{ color: '#b8832a' }}>Loading...</p>}

      {!loading && queue.length === 0 && (
        <p style={{ color: '#999', textAlign: 'center', marginTop: 40 }}>No pending GIFs.</p>
      )}

      {queue.map(gif => (
        <div key={gif.id} style={{
          background: '#fff', borderRadius: 12, marginBottom: 20,
          overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}>
          <img src={gif.gif_url} alt={gif.title} style={{ width: '100%', display: 'block', maxHeight: 300, objectFit: 'contain' }} />
          <div style={{ padding: 16 }}>
            <h3 style={{ marginBottom: 6 }}>{gif.title}</h3>
            {gif.description && <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: 8 }}>{gif.description}</p>}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
              {gif.tags.map(t => <TagChip key={t} tag={t} />)}
            </div>
            <p style={{ fontSize: '0.82rem', color: '#888', marginBottom: 12 }}>
              By {gif.submitter_name}{gif.submitter_email ? ` (${gif.submitter_email})` : ''} ·{' '}
              <a href={gif.source_url} target="_blank" rel="noreferrer" style={{ color: '#d4880a' }}>
                Source ({gif.source_start}s – {gif.source_end}s)
              </a>
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => handleApprove(gif.id)}
                disabled={actionInProgress === gif.id}
                style={{ flex: 1, background: actionInProgress === gif.id ? '#ccc' : '#27ae60', color: '#fff', border: 'none', borderRadius: 8, padding: '10px', fontWeight: 700, cursor: actionInProgress === gif.id ? 'not-allowed' : 'pointer' }}>
                Approve
              </button>
              <button
                onClick={() => handleReject(gif.id)}
                disabled={actionInProgress === gif.id}
                style={{ flex: 1, background: actionInProgress === gif.id ? '#ccc' : '#e74c3c', color: '#fff', border: 'none', borderRadius: 8, padding: '10px', fontWeight: 700, cursor: actionInProgress === gif.id ? 'not-allowed' : 'pointer' }}>
                Reject
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
