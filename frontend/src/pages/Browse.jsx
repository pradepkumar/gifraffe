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
        <p style={{ color: '#b8832a', fontSize: '0.9rem' }}>
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
                background: active ? '#d4880a' : '#f5e6c0',
                color: active ? '#fff' : '#7a4f1a',
                border: 'none', borderRadius: 20,
                padding: '6px 16px', fontWeight: 600,
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
              flex: 1, padding: '12px 16px', borderRadius: 10,
              border: '2px solid #e8c97a', fontSize: '1rem',
              background: '#fffdf5',
            }}
          />
          <button type="submit" style={{
            background: '#d4880a', color: '#fff', border: 'none',
            borderRadius: 10, padding: '12px 20px', fontWeight: 700,
            cursor: 'pointer', fontSize: '1rem',
          }}>
            Search
          </button>
        </div>
      </form>

      {loading && <p style={{ textAlign: 'center', color: '#b8832a' }}>Loading...</p>}
      {error && <p style={{ textAlign: 'center', color: '#c0392b' }}>{error}</p>}

      {!loading && gifs.length === 0 && (
        <p style={{ textAlign: 'center', color: '#999', marginTop: 40 }}>
          No GIFs found. <a href="/make" style={{ color: '#d4880a' }}>Make one!</a>
        </p>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 16,
      }}>
        {gifs.map(gif => (
          <GifCard
            key={gif.id}
            gif={gif}
            onTagClick={handleTagClick}
            onClick={setSelected}
          />
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
