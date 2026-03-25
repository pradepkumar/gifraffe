import { useState } from 'react'

const fieldStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)',
  border: '2px solid var(--color-amber-muted)', fontSize: '0.95rem',
  background: 'var(--color-cream-card)', resize: 'vertical',
  boxSizing: 'border-box',
}

const labelStyle = {
  display: 'block', marginBottom: 4, fontSize: '0.85rem',
  fontWeight: 600, color: 'var(--color-brown-mid)',
}

export default function MetadataForm({ onSubmit, loading, categories }) {
  const [form, setForm] = useState({
    title: '', tags: '', submitter_name: '', description: '', submitter_email: '', category: ''
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
      <div>
        <label style={labelStyle}>Category *</label>
        <select
          value={form.category}
          onChange={e => set('category', e.target.value)}
          required
          style={{ ...fieldStyle, cursor: 'pointer', resize: 'none' }}
        >
          <option value="" disabled>Select a category</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
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
          background: loading ? 'var(--color-disabled)' : 'var(--color-amber)',
          color: loading ? 'var(--color-disabled-text)' : '#fff', border: 'none', borderRadius: 'var(--radius-md)',
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
  return (
    <div>
      <label style={labelStyle}>
        {label}
      </label>
      {multiline
        ? <textarea value={value} onChange={e => onChange(e.target.value)} required={required} style={{ ...fieldStyle, minHeight: 80 }} />
        : <input type={type} value={value} onChange={e => onChange(e.target.value)} required={required} style={fieldStyle} />
      }
    </div>
  )
}
