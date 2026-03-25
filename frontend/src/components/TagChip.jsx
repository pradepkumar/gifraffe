export default function TagChip({ tag, onClick }) {
  return (
    <span
      onClick={() => onClick?.(tag)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(tag) } } : undefined}
      style={{
        background: 'var(--color-cream-chip)',
        color: 'var(--color-brown-light)',
        borderRadius: 'var(--radius-pill)',
        padding: '3px 10px',
        fontSize: 'var(--text-xs)',
        fontWeight: 600,
        cursor: onClick ? 'pointer' : 'default',
        userSelect: 'none',
        border: '1px solid var(--color-amber-muted)',
      }}
    >
      {tag}
    </span>
  )
}
