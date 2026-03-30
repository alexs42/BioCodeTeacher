import { useState } from 'react'
import { Sun, Moon, FolderOpen, Settings, Microscope, HardDrive } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import { loadLocalRepo, loadGithubRepo } from '../../services/api'
import FolderBrowser from './FolderBrowser'

export default function Header() {
  const {
    isDarkMode,
    toggleDarkMode,
    repoPath,
    setRepo,
    clearRepo,
    apiKey,
    githubToken,
    setShowSettingsModal,
    setHasCachedAnalysis,
  } = useCodeStore()

  const [isLoading, setIsLoading] = useState(false)
  const [showRepoInput, setShowRepoInput] = useState(false)
  const [showBrowser, setShowBrowser] = useState(false)
  const [repoInput, setRepoInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleLoadRepo = async (pathOverride?: string) => {
    const path = pathOverride || repoInput.trim()
    if (!path) return

    setIsLoading(true)
    setError(null)

    try {
      const isGithub = path.startsWith('https://github.com') || path.startsWith('github.com')

      const result = isGithub
        ? await loadGithubRepo(path, githubToken || undefined)
        : await loadLocalRepo(path)

      setRepo(result.repo_id, result.root_path, result.file_tree)
      if (result.has_cached_analysis) {
        setHasCachedAnalysis(true)
      }
      setShowRepoInput(false)
      setShowBrowser(false)
      setRepoInput('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load repository')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBrowseSelect = (path: string) => {
    setShowBrowser(false)
    handleLoadRepo(path)
  }

  return (
    <header className="flex-shrink-0 relative">
      {/* Main header bar */}
      <div
        className="h-14 flex items-center px-5 gap-5 relative z-10"
        style={{
          background: 'linear-gradient(180deg, var(--ct-surface) 0%, rgba(12,17,24,0.95) 100%)',
          borderBottom: '1px solid rgba(45,212,191,0.08)',
        }}
      >
        {/* Logo cluster — microscope + glowing "Bio" */}
        <div className="flex items-center gap-2.5 group cursor-default select-none">
          {/* Microscope icon with ambient glow */}
          <div className="relative">
            <Microscope
              className="w-[22px] h-[22px] relative z-10 transition-all duration-300 group-hover:scale-110"
              style={{ color: 'var(--ct-primary)' }}
            />
            {/* Ambient glow behind icon */}
            <div
              className="absolute inset-0 rounded-full blur-md opacity-40 group-hover:opacity-70 transition-opacity duration-500"
              style={{ background: 'var(--ct-primary)', transform: 'scale(1.8)' }}
            />
          </div>

          {/* Wordmark */}
          <div className="flex items-baseline gap-0 font-display">
            {/* "Bio" — glowing teal, slightly heavier */}
            <span
              className="text-[1.15rem] font-bold tracking-tight"
              style={{
                color: 'var(--ct-primary)',
                textShadow: '0 0 20px rgba(45,212,191,0.35), 0 0 4px rgba(45,212,191,0.15)',
              }}
            >
              Bio
            </span>
            {/* "CodeTeacher" — crisp white, thinner */}
            <span
              className="text-[1.15rem] font-semibold tracking-tight"
              style={{ color: 'var(--ct-text)' }}
            >
              CodeTeacher
            </span>
          </div>

          {/* Subtle version / domain tag */}
          <span
            className="text-[0.6rem] font-mono uppercase tracking-[0.15em] px-1.5 py-0.5 rounded ml-1 hidden sm:inline-block"
            style={{
              color: 'var(--ct-primary)',
              background: 'rgba(45,212,191,0.08)',
              border: '1px solid rgba(45,212,191,0.12)',
            }}
          >
            scRNA-seq
          </span>
        </div>

        {/* Vertical divider */}
        <div
          className="w-px h-6 hidden sm:block"
          style={{ background: 'linear-gradient(180deg, transparent, var(--ct-border), transparent)' }}
        />

        {/* Repo info or load button */}
        <div className="flex-1 flex items-center gap-2 min-w-0">
          {repoPath ? (
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg max-w-md"
              style={{
                background: 'rgba(6,10,16,0.7)',
                border: '1px solid var(--ct-border)',
              }}
            >
              <FolderOpen className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--ct-accent)' }} />
              <span className="text-sm truncate" style={{ color: 'var(--ct-text-secondary)' }}>
                {repoPath}
              </span>
              <button
                onClick={clearRepo}
                className="text-xs ml-2 flex-shrink-0 transition-colors duration-200"
                style={{ color: 'var(--ct-text-secondary)' }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--ct-text)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--ct-text-secondary)')}
              >
                Close
              </button>
            </div>
          ) : showRepoInput ? (
            <div className="flex items-center gap-2 flex-1 max-w-xl">
              <input
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLoadRepo()}
                placeholder="Path to Scanpy project, Snakemake pipeline, or GitHub URL..."
                className="flex-1 px-3 py-1.5 rounded-lg text-sm transition-colors duration-200"
                style={{
                  background: 'var(--ct-bg)',
                  border: '1px solid var(--ct-border)',
                  color: 'var(--ct-text)',
                  outline: 'none',
                }}
                onFocus={e => (e.currentTarget.style.borderColor = 'var(--ct-primary)')}
                onBlur={e => (e.currentTarget.style.borderColor = 'var(--ct-border)')}
                autoFocus
              />
              <button
                onClick={() => setShowBrowser(true)}
                className="px-3 py-1.5 rounded-lg text-sm transition-colors duration-200"
                title="Browse folders"
                style={{
                  background: 'var(--ct-bg)',
                  border: '1px solid var(--ct-border)',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--ct-primary)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--ct-border)')}
              >
                <HardDrive className="w-4 h-4" style={{ color: 'var(--ct-text-secondary)' }} />
              </button>
              <button
                onClick={() => handleLoadRepo()}
                disabled={isLoading}
                className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
                style={{
                  background: 'var(--ct-primary)',
                  color: '#060a10',
                }}
              >
                {isLoading ? 'Loading...' : 'Load'}
              </button>
              <button
                onClick={() => { setShowRepoInput(false); setError(null) }}
                className="transition-colors duration-200"
                style={{ color: 'var(--ct-text-secondary)' }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--ct-text)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--ct-text-secondary)')}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowRepoInput(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-200"
              style={{
                background: 'rgba(6,10,16,0.5)',
                border: '1px solid var(--ct-border)',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--ct-primary)'
                e.currentTarget.style.background = 'rgba(45,212,191,0.04)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--ct-border)'
                e.currentTarget.style.background = 'rgba(6,10,16,0.5)'
              }}
            >
              <FolderOpen className="w-4 h-4" style={{ color: 'var(--ct-text-secondary)' }} />
              <span className="text-sm" style={{ color: 'var(--ct-text-secondary)' }}>Open Repository</span>
            </button>
          )}

          {error && (
            <span className="text-red-400 text-sm flex-shrink-0">{error}</span>
          )}
        </div>

        {/* Right actions — instrument panel buttons */}
        <div className="flex items-center gap-1">
          {!apiKey && (
            <span
              className="text-xs mr-2 px-2 py-0.5 rounded font-mono"
              style={{
                color: 'var(--ct-warm)',
                background: 'rgba(245,158,11,0.08)',
                border: '1px solid rgba(245,158,11,0.15)',
              }}
            >
              API key required
            </span>
          )}

          <button
            onClick={() => setShowSettingsModal(true)}
            className="p-2 rounded-lg transition-all duration-200 group/btn"
            title="Settings"
            style={{ background: 'transparent' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(45,212,191,0.06)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            <Settings className="w-[18px] h-[18px] transition-colors duration-200" style={{ color: 'var(--ct-text-secondary)' }} />
          </button>

          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg transition-all duration-200"
            title={isDarkMode ? 'Light mode' : 'Dark mode'}
            style={{ background: 'transparent' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(45,212,191,0.06)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            {isDarkMode ? (
              <Sun className="w-[18px] h-[18px]" style={{ color: 'var(--ct-text-secondary)' }} />
            ) : (
              <Moon className="w-[18px] h-[18px]" style={{ color: 'var(--ct-text-secondary)' }} />
            )}
          </button>
        </div>

        {showBrowser && (
          <FolderBrowser
            onSelect={handleBrowseSelect}
            onClose={() => setShowBrowser(false)}
          />
        )}
      </div>

      {/* Emission line — animated teal-indigo gradient glow */}
      <div className="header-glow relative overflow-hidden">
        <div className="header-glow-sweep" />
      </div>
    </header>
  )
}
