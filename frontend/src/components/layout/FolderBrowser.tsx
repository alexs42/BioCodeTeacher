import { useState, useEffect } from 'react'
import { Folder, ChevronRight, ArrowUp, X, Search } from 'lucide-react'
import { browseDirectory, DirectoryEntry } from '../../services/api'

interface FolderBrowserProps {
  onSelect: (path: string) => void
  onClose: () => void
}

export default function FolderBrowser({ onSelect, onClose }: FolderBrowserProps) {
  const [currentPath, setCurrentPath] = useState('')
  const [directories, setDirectories] = useState<DirectoryEntry[]>([])
  const [parentPath, setParentPath] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pathInput, setPathInput] = useState('')

  const loadDirectory = async (path: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await browseDirectory(path)
      setCurrentPath(result.current)
      setParentPath(result.parent)
      setDirectories(result.directories)
      setPathInput(result.current)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to browse')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDirectory('')
  }, [])

  const handleNavigate = (path: string) => {
    loadDirectory(path)
  }

  const handleGoUp = () => {
    if (parentPath !== null) {
      loadDirectory(parentPath)
    } else {
      loadDirectory('')
    }
  }

  const handlePathSubmit = () => {
    if (pathInput.trim()) {
      loadDirectory(pathInput.trim())
    }
  }

  const handleSelect = () => {
    if (currentPath) {
      onSelect(currentPath)
    }
  }

  // Build breadcrumb segments from current path
  const breadcrumbs = currentPath
    ? currentPath.replace(/\\/g, '/').split('/').filter(Boolean)
    : []

  const buildBreadcrumbPath = (index: number) => {
    const segments = currentPath.replace(/\\/g, '/').split('/').filter(Boolean)
    const path = segments.slice(0, index + 1).join('/')
    // Preserve Windows drive letter format
    if (segments[0]?.match(/^[A-Z]:$/i)) {
      return segments.slice(0, index + 1).join('\\') + '\\'
    }
    return '/' + path
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-ct-surface border border-ct-border rounded-xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-ct-border">
          <h2 className="text-lg font-semibold">Browse Folders</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-ct-bg rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-ct-text-secondary" />
          </button>
        </div>

        {/* Path input */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-ct-border">
          <Search className="w-4 h-4 text-ct-text-secondary flex-shrink-0" />
          <input
            type="text"
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handlePathSubmit()}
            placeholder="Type a path..."
            className="flex-1 px-2 py-1 bg-ct-bg border border-ct-border rounded text-sm focus:outline-none focus:border-ct-primary"
          />
          <button
            onClick={handlePathSubmit}
            className="px-2 py-1 text-xs bg-ct-bg border border-ct-border rounded hover:border-ct-primary"
          >
            Go
          </button>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center gap-1 px-4 py-2 text-xs text-ct-text-secondary overflow-x-auto flex-shrink-0">
          <button
            onClick={() => loadDirectory('')}
            className="hover:text-ct-primary flex-shrink-0"
          >
            Root
          </button>
          {breadcrumbs.map((segment, i) => (
            <span key={i} className="flex items-center gap-1 flex-shrink-0">
              <ChevronRight className="w-3 h-3" />
              <button
                onClick={() => handleNavigate(buildBreadcrumbPath(i))}
                className="hover:text-ct-primary truncate max-w-[120px]"
                title={segment}
              >
                {segment}
              </button>
            </span>
          ))}
        </div>

        {/* Directory list */}
        <div className="flex-1 overflow-y-auto min-h-0 px-2 py-1">
          {loading ? (
            <div className="flex items-center justify-center py-8 text-ct-text-secondary text-sm">
              Loading...
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8 text-red-400 text-sm">
              {error}
            </div>
          ) : directories.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-ct-text-secondary text-sm">
              No subdirectories
            </div>
          ) : (
            directories.map((dir) => (
              <button
                key={dir.path}
                onClick={() => handleNavigate(dir.path)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-ct-bg text-left text-sm transition-colors group"
              >
                <Folder className="w-4 h-4 text-ct-accent flex-shrink-0" />
                <span className="truncate">{dir.name}</span>
                <ChevronRight className="w-3 h-3 text-ct-text-secondary ml-auto opacity-0 group-hover:opacity-100 flex-shrink-0" />
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-ct-border">
          <button
            onClick={handleGoUp}
            disabled={!parentPath && !currentPath}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-ct-bg border border-ct-border rounded-lg hover:border-ct-primary disabled:opacity-40 transition-colors"
          >
            <ArrowUp className="w-4 h-4" />
            Up
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm text-ct-text-secondary hover:text-ct-text transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSelect}
              disabled={!currentPath}
              className="px-4 py-1.5 text-sm bg-ct-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-colors"
            >
              Select This Folder
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
