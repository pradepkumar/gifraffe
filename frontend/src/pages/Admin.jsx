import { useState, useEffect } from 'react'
import { adminLogin, getAdminQueue, approveGif, rejectGif } from '../api.js'
import { CATEGORIES } from '../constants.js'

const inlineInputStyle = {
  width: '100%',
  padding: '8px 10px',
  borderRadius: 'var(--radius-sm)',
  border: '2px solid var(--color-amber-muted)',
  background: 'var(--color-cream-card)',
  fontSize: '0.9rem',
  boxSizing: 'border-box',
}

export default function Admin() {
  const [authed, setAuthed] = useState(false)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState(null)
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionInProgress, setActionInProgress] = useState(null)
  const [edits, setEdits] = useState({})

  const toEdits = (results) =>
    Object.fromEntries(results.map(g => [g.id, {
      title: g.title,
      tags: (g.tags ?? []).join(', '),
      description: g.description ?? '',
      category: g.category ?? 'Other',
    }]))

  const loadQueue = async () => {
    setLoading(true)
    try {
      const data = await getAdminQueue()
      setQueue(data.results)
      setEdits(toEdits(data.results))
    } catch (e) {
      if (e.message === 'Unauthorized') setAuthed(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Try to load queue — if it works, we're already authed (existing session)
    getAdminQueue()
      .then(data => { setAuthed(true); setQueue(data.results); setEdits(toEdits(data.results)) })
      .catch(() => {})
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
      const { title, tags, description, category } = edits[id] ?? {}
      await approveGif(id, {
        title: title?.trim() || undefined,
        tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
        description: description?.trim() || undefined,
        category: category || undefined,
      })
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
        <h2 style={{ marginBottom: 20, color: 'var(--color-brown-mid)' }}>Admin Login</h2>
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            aria-label="Admin password"
            required
            style={{ padding: '12px', borderRadius: 'var(--radius-md)', border: '2px solid var(--color-amber-muted)', fontSize: '1rem' }}
          />
          {loginError && <p style={{ color: 'var(--color-error)', fontSize: '0.9rem' }}>{loginError}</p>}
          <button type="submit" style={{ background: 'var(--color-amber)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: 13, fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}>
            Login
          </button>
        </form>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ color: 'var(--color-brown-mid)' }}>Approval Queue</h2>
        <button onClick={loadQueue} style={{ background: 'var(--color-cream-chip)', border: 'none', borderRadius: 'var(--radius-sm)', padding: '8px 14px', cursor: 'pointer', fontWeight: 600 }}>
          Refresh
        </button>
      </div>

      {loading && <p style={{ color: 'var(--color-brown-faint)' }}>Loading...</p>}

      {!loading && queue.length === 0 && (
        <p style={{ color: 'var(--color-brown-faint)', textAlign: 'center', marginTop: 40 }}>No pending GIFs.</p>
      )}

      {queue.map(gif => (
        <div key={gif.id} style={{
          background: '#fff', borderRadius: 'var(--radius-lg)', marginBottom: 20,
          overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}>
          <img src={gif.gif_url} alt={gif.title} style={{ width: '100%', display: 'block', maxHeight: 300, objectFit: 'contain' }} />
          <div style={{ padding: 16 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
              <input
                type="text"
                value={edits[gif.id]?.title ?? ''}
                onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], title: e.target.value } }))}
                style={inlineInputStyle}
                placeholder="Title"
                aria-label="GIF title"
              />
              <input
                type="text"
                value={edits[gif.id]?.tags ?? ''}
                onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], tags: e.target.value } }))}
                style={inlineInputStyle}
                placeholder="tag1, tag2"
                aria-label="Tags (comma separated)"
              />
              <textarea
                value={edits[gif.id]?.description ?? ''}
                onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], description: e.target.value } }))}
                style={{ ...inlineInputStyle, resize: 'vertical', minHeight: 60 }}
                placeholder="Description (optional)"
                aria-label="Description"
              />
              <select
                value={edits[gif.id]?.category ?? 'Other'}
                onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], category: e.target.value } }))}
                style={inlineInputStyle}
                aria-label="Category"
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-brown-faint)', marginBottom: 12 }}>
              By {gif.submitter_name}{gif.submitter_email ? ` (${gif.submitter_email})` : ''} ·{' '}
              <a href={gif.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-amber)' }}>
                Source ({gif.source_start}s – {gif.source_end}s)
              </a>
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => handleApprove(gif.id)}
                disabled={actionInProgress === gif.id}
                style={{ flex: 1, background: actionInProgress === gif.id ? 'var(--color-disabled)' : 'var(--color-success)', color: actionInProgress === gif.id ? 'var(--color-disabled-text)' : '#fff', border: 'none', borderRadius: 'var(--radius-sm)', padding: '10px', fontWeight: 700, cursor: actionInProgress === gif.id ? 'not-allowed' : 'pointer' }}>
                Approve
              </button>
              <button
                onClick={() => handleReject(gif.id)}
                disabled={actionInProgress === gif.id}
                style={{ flex: 1, background: actionInProgress === gif.id ? 'var(--color-disabled)' : 'var(--color-error)', color: actionInProgress === gif.id ? 'var(--color-disabled-text)' : '#fff', border: 'none', borderRadius: 'var(--radius-sm)', padding: '10px', fontWeight: 700, cursor: actionInProgress === gif.id ? 'not-allowed' : 'pointer' }}>
                Reject
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
