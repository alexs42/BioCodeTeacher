import { useState, useEffect, useCallback, useRef } from 'react'
import { APP_VERSION, CHANGELOG } from '../../config/version'

/**
 * Full-screen splash overlay shown on app launch.
 * Dismiss: press SPACE twice (debounced) or click the skip button.
 */
export default function SplashScreen({ onDismiss }: { onDismiss: () => void }) {
  const [fadeOut, setFadeOut] = useState(false)
  const [spaceCount, setSpaceCount] = useState(0)
  const [showChangelog, setShowChangelog] = useState(false)
  const spaceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const dismiss = useCallback(() => {
    setFadeOut(true)
    setTimeout(onDismiss, 600)
  }, [onDismiss])

  // Double-spacebar handler
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code !== 'Space') return
      e.preventDefault()

      setSpaceCount(prev => {
        const next = prev + 1
        if (next >= 2) {
          dismiss()
          return 0
        }
        // Reset after 800ms if second press doesn't come
        if (spaceTimerRef.current) clearTimeout(spaceTimerRef.current)
        spaceTimerRef.current = setTimeout(() => setSpaceCount(0), 800)
        return next
      })
    }
    window.addEventListener('keydown', handler)
    return () => {
      window.removeEventListener('keydown', handler)
      if (spaceTimerRef.current) clearTimeout(spaceTimerRef.current)
    }
  }, [dismiss])

  const currentChanges = CHANGELOG[0]

  return (
    <div
      className="splash-overlay"
      style={{ opacity: fadeOut ? 0 : 1, pointerEvents: fadeOut ? 'none' : 'auto' }}
    >
      {/* Animated background particles */}
      <div className="splash-particles" aria-hidden="true">
        {Array.from({ length: 24 }).map((_, i) => (
          <div
            key={i}
            className="splash-particle"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 8}s`,
              animationDuration: `${6 + Math.random() * 8}s`,
              '--particle-size': `${2 + Math.random() * 4}px`,
              '--particle-color': i % 3 === 0
                ? 'rgba(45,212,191,0.4)'
                : i % 3 === 1
                  ? 'rgba(129,140,248,0.3)'
                  : 'rgba(52,211,153,0.25)',
            } as React.CSSProperties}
          />
        ))}
      </div>

      {/* DNA helix decoration */}
      <svg className="splash-helix" viewBox="0 0 120 600" aria-hidden="true">
        <defs>
          <linearGradient id="helixGradT" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0" />
            <stop offset="30%" stopColor="#2dd4bf" stopOpacity="0.6" />
            <stop offset="70%" stopColor="#818cf8" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="helixGradB" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0" />
            <stop offset="30%" stopColor="#818cf8" stopOpacity="0.5" />
            <stop offset="70%" stopColor="#2dd4bf" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Double helix strands */}
        <path
          d={Array.from({ length: 20 }, (_, i) => {
            const y = i * 30
            const x = 60 + Math.sin(i * 0.6) * 35
            return `${i === 0 ? 'M' : 'S'} ${60 + Math.sin((i - 0.5) * 0.6) * 35},${y - 15} ${x},${y}`
          }).join(' ')}
          fill="none" stroke="url(#helixGradT)" strokeWidth="2.5" className="splash-helix-strand"
        />
        <path
          d={Array.from({ length: 20 }, (_, i) => {
            const y = i * 30
            const x = 60 - Math.sin(i * 0.6) * 35
            return `${i === 0 ? 'M' : 'S'} ${60 - Math.sin((i - 0.5) * 0.6) * 35},${y - 15} ${x},${y}`
          }).join(' ')}
          fill="none" stroke="url(#helixGradB)" strokeWidth="2.5" className="splash-helix-strand"
        />
        {/* Base pair rungs */}
        {Array.from({ length: 20 }, (_, i) => {
          const y = i * 30
          const x1 = 60 + Math.sin(i * 0.6) * 35
          const x2 = 60 - Math.sin(i * 0.6) * 35
          const depth = Math.cos(i * 0.6)
          if (Math.abs(depth) < 0.3) return null
          return (
            <line
              key={i} x1={x1} y1={y} x2={x2} y2={y}
              stroke={depth > 0 ? 'rgba(45,212,191,0.2)' : 'rgba(129,140,248,0.15)'}
              strokeWidth="1.5" strokeDasharray="3 4"
            />
          )
        })}
      </svg>

      {/* Main content */}
      <div className="splash-content">
        {/* Microscope icon */}
        <div className="splash-icon">
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="32" r="30" stroke="#2dd4bf" strokeWidth="1" opacity="0.2" />
            <circle cx="32" cy="32" r="22" stroke="#818cf8" strokeWidth="0.5" opacity="0.15" />
            {/* Microscope body */}
            <path d="M28 46h8M24 46h16" stroke="#2dd4bf" strokeWidth="2" strokeLinecap="round" />
            <path d="M32 46V38" stroke="#2dd4bf" strokeWidth="2" strokeLinecap="round" />
            <path d="M32 38l-6-16" stroke="#2dd4bf" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="26" cy="22" r="3" stroke="#818cf8" strokeWidth="1.5" fill="none" />
            <path d="M26 19v-4" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" />
            {/* Eyepiece */}
            <rect x="23" y="13" width="6" height="3" rx="1" fill="#818cf8" opacity="0.4" />
            {/* Stage */}
            <path d="M28 38h8" stroke="#2dd4bf" strokeWidth="1.5" strokeLinecap="round" />
            {/* Light dot */}
            <circle cx="32" cy="41" r="1.5" fill="#2dd4bf" opacity="0.6" />
          </svg>
        </div>

        {/* Wordmark */}
        <h1 className="splash-title">
          <span className="splash-title-bio">Bio</span>
          <span className="splash-title-sep">|</span>
          <span className="splash-title-code">CodeTeacher</span>
        </h1>

        {/* Version badge */}
        <div className="splash-version">
          <span className="splash-version-label">v{APP_VERSION}</span>
        </div>

        {/* Description */}
        <p className="splash-description">
          AI-powered bioinformatics code educator for single-cell,
          spatial transcriptomics, and digital pathology analysis
        </p>

        {/* Changelog toggle */}
        <button
          className="splash-changelog-toggle"
          onClick={() => setShowChangelog(!showChangelog)}
        >
          {showChangelog ? 'Hide' : 'Show'} what's new in v{APP_VERSION}
        </button>

        {showChangelog && currentChanges && (
          <div className="splash-changelog">
            <ul>
              {currentChanges.changes.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        )}

        {/* License */}
        <p className="splash-license">
          Freely distributed for non-commercial use under{' '}
          <a
            href="https://creativecommons.org/licenses/by-nc/4.0/"
            target="_blank"
            rel="noopener noreferrer"
          >CC BY-NC 4.0</a>.
          No warranty expressed or implied.
        </p>

        {/* Skip hint */}
        <div className="splash-skip">
          <span className={`splash-skip-dot ${spaceCount >= 1 ? 'active' : ''}`} />
          <span className={`splash-skip-dot ${spaceCount >= 2 ? 'active' : ''}`} />
          <span className="splash-skip-text">
            Press <kbd>SPACE</kbd> twice to continue
          </span>
        </div>

        <button className="splash-skip-btn" onClick={dismiss}>
          Skip
        </button>
      </div>
    </div>
  )
}
