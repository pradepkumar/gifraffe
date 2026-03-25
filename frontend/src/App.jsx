import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Browse from './pages/Browse.jsx'
import Make from './pages/Make.jsx'
import Admin from './pages/Admin.jsx'

const styles = {
  header: {
    background: 'var(--color-amber)',
    padding: '12px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
  },
  logo: {
    color: '#fff',
    fontWeight: 800,
    fontSize: '1.5rem',
    textDecoration: 'none',
    letterSpacing: '-0.5px',
  },
  nav: { display: 'flex', gap: 20 },
  navLink: {
    color: '#fff3d0',
    textDecoration: 'none',
    fontWeight: 500,
    fontSize: '0.95rem',
  },
}

export default function App() {
  return (
    <BrowserRouter>
      <header style={styles.header}>
        <Link to="/" style={styles.logo}>🦒 Gifraffe</Link>
        <nav style={styles.nav}>
          <Link to="/" style={styles.navLink}>Browse</Link>
          <Link to="/make" style={styles.navLink}>Make a GIF</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Browse />} />
        <Route path="/make" element={<Make />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  )
}
