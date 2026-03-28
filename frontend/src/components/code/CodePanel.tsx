import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import FileTree from './FileTree'
import CodeEditor from './CodeEditor'
import { useCodeStore } from '../../store/codeStore'

export default function CodePanel() {
  const { fileTree, currentFile } = useCodeStore()
  const [showTree, setShowTree] = useState(true)

  if (!fileTree) {
    return (
      <div className="h-full flex items-center justify-center bg-ct-bg text-ct-text-secondary">
        <div className="text-center space-y-4 p-8">
          <div className="text-4xl">📂</div>
          <h3 className="text-lg font-medium text-ct-text">No Repository Loaded</h3>
          <p className="text-sm max-w-xs">
            Click "Open Repository" in the header to load a local folder or clone from GitHub.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex bg-ct-bg">
      {/* File Tree Sidebar */}
      <div
        className={`${
          showTree ? 'w-64' : 'w-0'
        } transition-all duration-200 overflow-hidden border-r border-ct-border flex-shrink-0`}
      >
        <FileTree />
      </div>

      {/* Toggle button */}
      <button
        onClick={() => setShowTree(!showTree)}
        className="w-6 flex-shrink-0 bg-ct-surface hover:bg-ct-border flex items-center justify-center border-r border-ct-border"
        title={showTree ? 'Hide file tree' : 'Show file tree'}
      >
        {showTree ? (
          <ChevronLeft className="w-4 h-4 text-ct-text-secondary" />
        ) : (
          <ChevronRight className="w-4 h-4 text-ct-text-secondary" />
        )}
      </button>

      {/* Code Editor */}
      <div className="flex-1 overflow-hidden">
        {currentFile ? (
          <CodeEditor />
        ) : (
          <div className="h-full flex items-center justify-center text-ct-text-secondary">
            <div className="text-center space-y-2">
              <div className="text-3xl">📄</div>
              <p className="text-sm">Select a file from the tree to view</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
