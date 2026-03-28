import { useState } from 'react'
import { Sun, Moon, FolderOpen, Settings, BookOpen, HardDrive } from 'lucide-react'
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
    <header className="flex-shrink-0">
      <div className="h-14 bg-ct-surface flex items-center px-4 gap-4">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <BookOpen className="w-6 h-6 text-ct-warm" />
        <span className="text-lg font-display font-bold tracking-tight">CodeTeacher</span>
      </div>

      {/* Repo info or load button */}
      <div className="flex-1 flex items-center gap-2">
        {repoPath ? (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-ct-bg rounded-lg border border-ct-border">
            <FolderOpen className="w-4 h-4 text-ct-accent" />
            <span className="text-sm text-ct-text-secondary truncate max-w-[300px]">
              {repoPath}
            </span>
            <button
              onClick={clearRepo}
              className="text-ct-text-secondary hover:text-ct-text text-xs ml-2"
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
              placeholder="Local path or GitHub URL..."
              className="flex-1 px-3 py-1.5 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
              autoFocus
            />
            <button
              onClick={() => setShowBrowser(true)}
              className="px-3 py-1.5 bg-ct-bg border border-ct-border rounded-lg text-sm hover:border-ct-primary transition-colors"
              title="Browse folders"
            >
              <HardDrive className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleLoadRepo()}
              disabled={isLoading}
              className="px-3 py-1.5 bg-ct-primary text-white rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Load'}
            </button>
            <button
              onClick={() => {
                setShowRepoInput(false)
                setError(null)
              }}
              className="text-ct-text-secondary hover:text-ct-text"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowRepoInput(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-ct-bg border border-ct-border rounded-lg hover:border-ct-primary transition-colors"
          >
            <FolderOpen className="w-4 h-4" />
            <span className="text-sm">Open Repository</span>
          </button>
        )}

        {error && (
          <span className="text-red-400 text-sm">{error}</span>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2">
        {!apiKey && (
          <span className="text-xs text-orange-400 mr-2">API key required</span>
        )}

        <button
          onClick={() => setShowSettingsModal(true)}
          className="p-2 hover:bg-ct-bg rounded-lg transition-colors"
          title="Settings"
        >
          <Settings className="w-5 h-5 text-ct-text-secondary" />
        </button>

        <button
          onClick={toggleDarkMode}
          className="p-2 hover:bg-ct-bg rounded-lg transition-colors"
          title={isDarkMode ? 'Light mode' : 'Dark mode'}
        >
          {isDarkMode ? (
            <Sun className="w-5 h-5 text-ct-text-secondary" />
          ) : (
            <Moon className="w-5 h-5 text-ct-text-secondary" />
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
      <div className="header-glow" />
    </header>
  )
}
