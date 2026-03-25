import { useState, useEffect, useCallback, useRef } from 'react'
import { searchGifs } from '../api.js'
import GifCard from '../components/GifCard.jsx'
import GifModal from '../components/GifModal.jsx'
import { CATEGORIES } from '../constants.js'

export default function Browse() {
  const [query, setQuery] = useState('')
  const [gifs, setGifs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [category, setCategory] = useState('')

  const load = useCallback(async (q, cat = '') => {
    setLoading(true)
    setError(null)
    try {
      const data = await searchGifs(q, 0, cat)
      setGifs(data.results)
      setTotal(data.total)
    } catch (e) {
      setError('Failed to load GIFs')
    } finally {
      setLoading(false)
    }
  }, [])

  const mounted = useRef(false)

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      load(query, category)
      return
    }
    const timer = setTimeout(() => load(query, category), 300)
    return () => clearTimeout(timer)
  }, [query, category, load])

  const handleSearch = (e) => {
    e.preventDefault()
    load(query, category)
  }

  const handleTagClick = (tag) => {
    setQuery(tag)
  }

  const handleModalClose = useCallback(() => setSelected(null), [])

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px 16px' }}>
      {/* Giraffe spot accent */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <p style={{ color: 'var(--color-brown-faint)', fontSize: '0.9rem' }}>
          {total > 0 ? `${total} GIF${total !== 1 ? 's' : ''} in the library` : 'Search or browse GIFs below'}
        </p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {['All', ...CATEGORIES].map(c => {
          const val = c === 'All' ? '' : c
          const active = category === val
          return (
            <button
              key={c}
              onClick={() => setCategory(val)}
              style={{
                background: active ? 'var(--color-amber)' : 'var(--color-cream-chip)',
                color: active ? '#fff' : 'var(--color-brown-light)',
                border: 'none', borderRadius: 'var(--radius-pill)',
                padding: '10px 18px', fontWeight: 600,
                cursor: 'pointer', fontSize: '0.9rem',
              }}
            >
              {c}
            </button>
          )
        })}
      </div>

      <form onSubmit={handleSearch} style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search GIFs by title, tags, description..."
            style={{
              flex: 1, padding: '12px 16px', borderRadius: 'var(--radius-md)',
              border: '2px solid var(--color-amber-muted)', fontSize: '1rem',
              background: 'var(--color-cream-card)',
            }}
          />
          <button type="submit" style={{
            background: 'var(--color-amber)', color: '#fff', border: 'none',
            borderRadius: 'var(--radius-md)', padding: '12px 20px', fontWeight: 700,
            cursor: 'pointer', fontSize: '1rem',
          }}>
            Search
          </button>
        </div>
      </form>

      {loading && (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}>
          <div style={{
            fontSize: '3rem',
            animation: 'gifraffe-bounce 1s ease-in-out infinite',
            display: 'inline-block',
          }}>
            🦒
          </div>
          <p style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-lg)',
            fontWeight: 700,
            color: 'var(--color-brown-mid)',
            margin: 0,
          }}>
            Loading GIFs...
          </p>
          <p style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--color-brown-faint)',
            margin: 0,
          }}>
            The giraffe is fetching them
          </p>
        </div>
      )}
      {error && <p style={{ textAlign: 'center', color: 'var(--color-error)' }}>{error}</p>}

      {!loading && gifs.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '64px 24px',
          maxWidth: 420,
          margin: '0 auto',
        }}>
          <div style={{ fontSize: '4rem', marginBottom: 16 }}>🦒</div>
          <h3 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-xl)',
            fontWeight: 800,
            color: 'var(--color-brown-mid)',
            margin: '0 0 10px',
          }}>
            {query || category ? 'No GIFs match that search' : 'The library is empty'}
          </h3>
          <p style={{
            fontSize: 'var(--text-base)',
            color: 'var(--color-brown-faint)',
            margin: '0 0 28px',
            lineHeight: 1.6,
          }}>
            {query || category
              ? 'Try different keywords or browse all categories.'
              : 'Be the first to add a GIF. Paste a YouTube URL and turn any moment into a GIF.'}
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            {(query || category) && (
              <button
                onClick={() => { setQuery(''); setCategory(''); }}
                style={{
                  background: 'var(--color-cream-chip)',
                  color: 'var(--color-brown-light)',
                  border: 'none',
                  borderRadius: 'var(--radius-pill)',
                  padding: '10px 22px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 'var(--text-base)',
                }}
              >
                Clear search
              </button>
            )}
            <a
              href="/make"
              style={{
                background: 'var(--color-amber)',
                color: '#fff',
                borderRadius: 'var(--radius-pill)',
                padding: '10px 22px',
                fontWeight: 700,
                fontSize: 'var(--text-base)',
                textDecoration: 'none',
                display: 'inline-block',
              }}
            >
              Make a GIF 🦒
            </a>
          </div>
        </div>
      )}

      <div className="gif-grid">
        {gifs.map(gif => (
          <div key={gif.id} className="gif-grid-item">
            <GifCard gif={gif} onTagClick={handleTagClick} onClick={setSelected} />
          </div>
        ))}
      </div>

      <GifModal
        gif={selected}
        onClose={handleModalClose}
        onTagClick={handleTagClick}
      />
    </div>
  )
}
