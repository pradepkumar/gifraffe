import { useState } from 'react'

export default function MetadataForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    title: '', tags: '', submitter_name: '', description: '', submitter_email: ''
  })

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Field label="Title *" value={form.title} onChange={v => set('title', v)} required />
      <Field
        label="Tags * (comma-separated, e.g. vijay,comedy,entry)"
        value={form.tags} onChange={v => set('tags', v)} required
      />
      <Field label="Your Name *" value={form.submitter_name} onChange={v => set('submitter_name', v)} required />
      <Field
        label="Description (dialogue, scene context...)"
        value={form.description} onChange={v => set('description', v)}
        multiline
      />
      <Field
        label="Email (optional)"
        value={form.submitter_email} onChange={v => set('submitter_email', v)}
        type="email"
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          background: loading ? '#ccc' : '#d4880a',
          color: '#fff', border: 'none', borderRadius: 10,
          padding: '12px', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '1rem', marginTop: 4,
        }}
      >
        {loading ? 'Submitting...' : 'Submit to Gifraffe'}
      </button>
    </form>
  )
}

function Field({ label, value, onChange, required, type = 'text', multiline }) {
  const style = {
    width: '100%', padding: '10px 12px', borderRadius: 8,
    border: '2px solid #e8c97a', fontSize: '0.95rem',
    outline: 'none', background: '#fffdf5', resize: 'vertical',
    boxSizing: 'border-box',
  }
  return (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: '0.85rem', fontWeight: 600, color: '#5a3a10' }}>
        {label}
      </label>
      {multiline
        ? <textarea value={value} onChange={e => onChange(e.target.value)} required={required} style={{ ...style, minHeight: 80 }} />
        : <input type={type} value={value} onChange={e => onChange(e.target.value)} required={required} style={style} />
      }
    </div>
  )
}
