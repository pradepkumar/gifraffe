import { useState, useEffect, useCallback } from 'react'
import { searchGifs } from '../api.js'
import GifCard from '../components/GifCard.jsx'
import GifModal from '../components/GifModal.jsx'

export default function Browse() {
  const [query, setQuery] = useState('')
  const [gifs, setGifs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = useCallback(async (q) => {
    setLoading(true)
    setError(null)
    try {
      const data = await searchGifs(q)
      setGifs(data.results)
      setTotal(data.total)
    } catch (e) {
      setError('Failed to load GIFs')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load('') }, [load])

  const handleSearch = (e) => {
    e.preventDefault()
    load(query)
  }

  const handleTagClick = (tag) => {
    setQuery(tag)
    load(tag)
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px 16px' }}>
      {/* Giraffe spot accent */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <p style={{ color: '#b8832a', fontSize: '0.9rem' }}>
          {total > 0 ? `${total} GIF${total !== 1 ? 's' : ''} in the library` : 'Search or browse GIFs below'}
        </p>
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
              outline: 'none', background: '#fffdf5',
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
        onClose={() => setSelected(null)}
        onTagClick={handleTagClick}
      />
    </div>
  )
}
