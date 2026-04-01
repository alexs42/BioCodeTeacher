import { useState } from 'react'
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react'
import { useCodeStore, FileNode } from '../../store/codeStore'
import { getFileContent } from '../../services/api'

// File type icons by language
const getFileIcon = (language?: string) => {
  const iconColors: Record<string, string> = {
    typescript: 'text-blue-400',
    javascript: 'text-yellow-400',
    python: 'text-green-400',
    rust: 'text-orange-400',
    go: 'text-cyan-400',
    java: 'text-red-400',
    html: 'text-orange-500',
    css: 'text-blue-500',
    json: 'text-yellow-300',
    markdown: 'text-ct-text-secondary',
  }

  const color = iconColors[language || ''] || 'text-ct-text-secondary'
  return <File className={`w-4 h-4 ${color}`} />
}

interface TreeNodeProps {
  node: FileNode
  depth: number
}

function TreeNode({ node, depth }: TreeNodeProps) {
  const [isOpen, setIsOpen] = useState(depth < 2) // Auto-expand first 2 levels
  const { currentFile, repoId, setCurrentFile } = useCodeStore()

  const isSelected = node.type === 'file' && currentFile === node.path

  const handleClick = async () => {
    if (node.type === 'directory') {
      setIsOpen(!isOpen)
    } else if (repoId) {
      try {
        const data = await getFileContent(repoId, node.path)
        setCurrentFile(data.path, data.content, data.language)
      } catch (e) {
        console.error('Failed to load file:', e)
      }
    }
  }

  return (
    <div>
      <div
        onClick={handleClick}
        className={`
          flex items-center gap-1 px-2 py-1 cursor-pointer text-sm
          hover:bg-ct-surface transition-colors
          ${isSelected ? 'bg-ct-primary/20 text-ct-primary' : 'text-ct-text'}
        `}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {node.type === 'directory' ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-4 h-4 text-ct-text-secondary flex-shrink-0" />
            ) : (
              <ChevronRight className="w-4 h-4 text-ct-text-secondary flex-shrink-0" />
            )}
            {isOpen ? (
              <FolderOpen className="w-4 h-4 text-ct-accent flex-shrink-0" />
            ) : (
              <Folder className="w-4 h-4 text-ct-accent flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-4" /> {/* Spacer for alignment */}
            {getFileIcon(node.language)}
          </>
        )}
        <span className="truncate">{node.name}</span>
      </div>

      {/* Children */}
      {node.type === 'directory' && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNode key={child.path} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileTree() {
  const { fileTree, repoPath } = useCodeStore()

  if (!fileTree) {
    return null
  }

  // Get the repo name from the path
  const repoName = repoPath?.split(/[\\/]/).pop() || 'Repository'

  return (
    <div className="h-full flex flex-col bg-ct-surface">
      {/* Header */}
      <div className="px-3 py-2 border-b border-ct-border">
        <h3 className="text-xs font-semibold text-ct-text-secondary uppercase tracking-wider">
          Explorer
        </h3>
        <p className="text-sm text-ct-text truncate mt-1" title={repoPath || ''}>
          {repoName}
        </p>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-auto py-1">
        {fileTree.children?.map((child) => (
          <TreeNode key={child.path} node={child} depth={0} />
        ))}
      </div>
    </div>
  )
}
