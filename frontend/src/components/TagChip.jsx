export default function TagChip({ tag, onClick }) {
  return (
    <span
      onClick={() => onClick?.(tag)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(tag) } } : undefined}
      style={{
        background: '#f5e6c0',
        color: '#7a4f1a',
        borderRadius: 20,
        padding: '3px 10px',
        fontSize: '0.78rem',
        fontWeight: 600,
        cursor: onClick ? 'pointer' : 'default',
        userSelect: 'none',
        border: '1px solid #e8c97a',
      }}
    >
      {tag}
    </span>
  )
}
