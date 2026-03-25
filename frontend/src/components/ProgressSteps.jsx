const STEPS = ['Downloading', 'Extracting clip', 'Converting to GIF', 'Done']

export default function ProgressSteps({ currentStep }) {
  const currentIdx = STEPS.indexOf(currentStep)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, margin: '20px 0' }}>
      {STEPS.map((step, i) => {
        const done = i < currentIdx || currentStep === 'Done'
        const active = step === currentStep && currentStep !== 'Done'
        return (
          <div key={step} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 0 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 60 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: done ? 'var(--color-amber)' : active ? 'var(--color-amber-light)' : 'var(--color-amber-muted)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontSize: '0.75rem', fontWeight: 700,
                transition: 'background 0.3s',
              }}>
                {done ? '✓' : i + 1}
              </div>
              <span style={{
                fontSize: '0.7rem', marginTop: 4, textAlign: 'center',
                color: done || active ? 'var(--color-brown-light)' : 'var(--color-brown-faint)',
                fontWeight: active ? 700 : 400,
              }}>
                {step}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{
                flex: 1, height: 2,
                background: done ? 'var(--color-amber)' : 'var(--color-amber-muted)',
                marginBottom: 20, transition: 'background 0.3s',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
