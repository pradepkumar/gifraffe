import { useEffect } from 'react'
import TagChip from './TagChip.jsx'

export default function GifModal({ gif, onClose, onTagClick }) {
  if (!gif) return null

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = gif.gif_url
    a.download = `${gif.title.replace(/\s+/g, '-')}.gif`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        const res = await fetch(gif.gif_url)
        const blob = await res.blob()
        const file = new File([blob], `${gif.title}.gif`, { type: 'image/gif' })
        await navigator.share({ files: [file], title: gif.title })
        return
      } catch {}
    }
    handleDownload()
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, padding: 16,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 16, maxWidth: 560,
          width: '100%', overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        }}
      >
        <img src={gif.gif_url} alt={gif.title} style={{ width: '100%', display: 'block' }} />
        <div style={{ padding: 16 }}>
          <h3 style={{ marginBottom: 8 }}>{gif.title}</h3>
          {gif.description && (
            <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: 10 }}>{gif.description}</p>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 14 }}>
            {(gif.tags ?? []).map(tag => (
              <TagChip key={tag} tag={tag} onClick={() => { onTagClick(tag); onClose() }} />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={handleDownload} style={btnStyle('#d4880a', '#fff')}>
              Download GIF
            </button>
            <button onClick={handleShare} style={btnStyle('#f5e6c0', '#7a4f1a')}>
              Share
            </button>
          </div>
          <p style={{ marginTop: 10, fontSize: '0.78rem', color: '#999' }}>
            Submitted by {gif.submitter_name}
          </p>
        </div>
      </div>
    </div>
  )
}

const btnStyle = (bg, color) => ({
  background: bg, color, border: 'none', borderRadius: 8,
  padding: '9px 18px', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem',
})
