const BASE = ''  // same origin in prod; Vite proxy handles /api in dev

export async function generateGif(url, start, end) {
  const res = await fetch(`${BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, start, end }),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function pollJob(jobId) {
  const res = await fetch(`${BASE}/api/jobs/${jobId}`)
  if (!res.ok) throw new Error('Job not found')
  return res.json()
}

export async function submitGif(payload) {
  const res = await fetch(`${BASE}/api/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function searchGifs(q = '', offset = 0) {
  const params = new URLSearchParams({ offset })
  if (q) params.set('q', q)
  const res = await fetch(`${BASE}/api/gifs?${params}`)
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}

export async function getGif(id) {
  const res = await fetch(`${BASE}/api/gifs/${id}`)
  if (!res.ok) throw new Error('GIF not found')
  return res.json()
}

export async function adminLogin(password) {
  const res = await fetch(`${BASE}/api/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Invalid password')
  return res.json()
}

export async function getAdminQueue() {
  const res = await fetch(`${BASE}/api/admin/queue`, { credentials: 'include' })
  if (res.status === 401) throw new Error('Unauthorized')
  return res.json()
}

export async function approveGif(id, fields = {}) {
  const res = await fetch(`${BASE}/api/admin/approve/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Approve failed')
  return res.json()
}

export async function rejectGif(id) {
  const res = await fetch(`${BASE}/api/admin/reject/${id}`, {
    method: 'POST', credentials: 'include'
  })
  if (!res.ok) throw new Error('Reject failed')
  return res.json()
}
