import { useState, useRef, useEffect } from 'react'
import { generateGif, pollJob, submitGif } from '../api.js'
import ProgressSteps from '../components/ProgressSteps.jsx'
import MetadataForm from '../components/MetadataForm.jsx'
import { CATEGORIES } from '../constants.js'

const STEP_LABELS = { pending: 'Downloading', processing: null, done: 'Done', failed: null }

function parseTime(val) {
  // Accept "mm:ss" or plain seconds
  if (val.includes(':')) {
    const [m, s] = val.split(':').map(Number)
    return m * 60 + s
  }
  return parseFloat(val) || 0
}

export default function Make() {
  const [url, setUrl] = useState('')
  const [startRaw, setStartRaw] = useState('')
  const [endRaw, setEndRaw] = useState('')
  const [state, setState] = useState('idle') // idle | generating | done | error | submitted
  const [currentStep, setCurrentStep] = useState(null)
  const [gifUrl, setGifUrl] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitDone, setSubmitDone] = useState(false)
  const [generatedAt, setGeneratedAt] = useState(null)
  const pollRef = useRef(null)

  const stopPolling = () => { clearInterval(pollRef.current) }

  const handleGenerate = async (e) => {
    e.preventDefault()
    setError(null)
    setGifUrl(null)
    setShowForm(false)
    setSubmitDone(false)
    setState('generating')
    setCurrentStep('Downloading')

    const start = parseTime(startRaw)
    const end = parseTime(endRaw)

    try {
      const { job_id } = await generateGif(url, start, end)
      setJobId(job_id)
      pollRef.current = setInterval(async () => {
        try {
          const job = await pollJob(job_id)
          if (job.step) setCurrentStep(job.step)
          if (job.status === 'done') {
            stopPolling()
            setGifUrl(job.gif_url)
            setCurrentStep('Done')
            setState('done')
            setGeneratedAt(Date.now())
          } else if (job.status === 'failed') {
            stopPolling()
            setError(job.error || 'Something went wrong — please try again')
            setState('error')
          }
        } catch (err) {
          stopPolling()
          setError(err.message || 'Lost connection — please try again')
          setState('error')
        }
      }, 2000)
    } catch (e) {
      setState('error')
      setError(e.message)
    }
  }

  useEffect(() => () => stopPolling(), [])

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = gifUrl
    a.download = 'gifraffe.gif'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        const res = await fetch(gifUrl)
        const blob = await res.blob()
        const file = new File([blob], 'gifraffe.gif', { type: 'image/gif' })
        await navigator.share({ files: [file], title: 'Check out this GIF from Gifraffe!' })
        return
      } catch {}
    }
    handleDownload()
  }

  const handleSubmit = async (formData) => {
    const expiredMs = 60 * 60 * 1000
    if (generatedAt && Date.now() - generatedAt > expiredMs) {
      setError('This GIF has expired — generate it again to submit')
      return
    }
    setSubmitLoading(true)
    try {
      await submitGif({
        job_id: jobId,
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
      })
      setSubmitDone(true)
      setShowForm(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 560, margin: '0 auto', padding: '24px 16px' }}>
      <h2 style={{ marginBottom: 6, color: 'var(--color-brown-mid)', fontFamily: 'var(--font-display)', fontWeight: 700 }}>Make a GIF</h2>
      <p style={{ color: 'var(--color-brown-faint)', marginBottom: 20, fontSize: 'var(--text-sm)' }}>
        Paste a YouTube URL, pick your moment (up to 10 seconds), and we'll turn it into a GIF.
      </p>

      <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          aria-label="YouTube URL"
          required
          style={inputStyle}
        />
        <div style={{ display: 'flex', gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Start time (seconds or mm:ss)</label>
            <input value={startRaw} onChange={e => setStartRaw(e.target.value)} placeholder="0" required style={inputStyle} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>End time (seconds or mm:ss)</label>
            <input value={endRaw} onChange={e => setEndRaw(e.target.value)} placeholder="5" required style={inputStyle} />
          </div>
        </div>
        <button
          type="submit"
          disabled={state === 'generating'}
          style={{
            background: state === 'generating' ? 'var(--color-disabled)' : 'var(--color-amber)',
            color: state === 'generating' ? 'var(--color-disabled-text)' : '#fff',
            border: 'none', borderRadius: 'var(--radius-md)', padding: '13px',
            fontWeight: 700, cursor: state === 'generating' ? 'not-allowed' : 'pointer',
            fontSize: '1rem',
          }}
        >
          {state === 'generating' ? 'Generating...' : 'Generate GIF'}
        </button>
      </form>

      {state === 'generating' && currentStep && (
        <ProgressSteps currentStep={currentStep} />
      )}

      {error && (
        <div style={{ background: 'var(--color-error-bg)', border: '1px solid var(--color-error-border)', borderRadius: 'var(--radius-md)', padding: 14, color: 'var(--color-error)', marginBottom: 16 }}>
          {error}
        </div>
      )}

      {state === 'done' && gifUrl && (
        <div>
          <img src={gifUrl} alt="Generated GIF" style={{ width: '100%', borderRadius: 'var(--radius-lg)', marginBottom: 14 }} />
          <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
            <button onClick={handleDownload} style={actionBtn('var(--color-amber)', '#fff')}>Download GIF</button>
            <button onClick={handleShare} style={actionBtn('var(--color-cream-chip)', 'var(--color-brown-light)')}>Share</button>
          </div>
          {!submitDone && !showForm && (
            <button onClick={() => setShowForm(true)} style={actionBtn('#fff', 'var(--color-amber)', '2px solid var(--color-amber)')}>
              Submit to Gifraffe
            </button>
          )}
          {submitDone && (
            <div style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success-border)', borderRadius: 'var(--radius-md)', padding: 14, color: 'var(--color-success)' }}>
              Submitted! It will appear in the library once approved.
            </div>
          )}
          {showForm && !submitDone && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ marginBottom: 14, color: 'var(--color-brown-mid)', fontFamily: 'var(--font-display)', fontWeight: 700 }}>Submit details</h3>
              <MetadataForm onSubmit={handleSubmit} loading={submitLoading} categories={CATEGORIES} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  width: '100%', padding: '11px 14px', borderRadius: 'var(--radius-md)',
  border: '2px solid var(--color-amber-muted)', fontSize: '1rem',
  background: 'var(--color-cream-card)',
  boxSizing: 'border-box',
}
const labelStyle = { display: 'block', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-brown-mid)', marginBottom: 4 }
const actionBtn = (bg, color, border = 'none') => ({
  background: bg, color, border, borderRadius: 'var(--radius-md)',
  padding: '11px 18px', fontWeight: 700, cursor: 'pointer',
  fontSize: '0.95rem', flex: 1,
})
