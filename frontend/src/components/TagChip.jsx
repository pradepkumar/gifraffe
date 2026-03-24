export default function TagChip({ tag, onClick }) {
  return (
    <span
      onClick={() => onClick?.(tag)}
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
