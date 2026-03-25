import TagChip from './TagChip.jsx'

export default function GifCard({ gif, onTagClick, onClick }) {
  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={gif.title}
      onClick={() => onClick(gif)}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(gif) } }}
      style={{
        background: '#fff',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        cursor: 'pointer',
        transition: 'transform 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
    >
      <img
        src={gif.gif_url}
        alt={gif.title}
        loading="lazy"
        style={{ width: '100%', display: 'block', aspectRatio: '16/9', objectFit: 'cover' }}
      />
      <div style={{ padding: '10px 12px' }}>
        <div style={{ fontWeight: 600, marginBottom: 6, fontSize: '0.9rem' }}>{gif.title}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {(gif.tags ?? []).map(tag => (
            <span key={tag} onClick={e => e.stopPropagation()}>
              <TagChip tag={tag} onClick={() => onTagClick?.(tag)} />
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
