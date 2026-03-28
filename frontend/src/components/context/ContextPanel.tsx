/**
 * Main right-panel component replacing ExplanationPanel.
 * Implements three-tier context display:
 *   Tier 1 (repo): RepoOverview
 *   Tier 2 (file): FileSummary
 *   Tier 3 (line): LineExplanation
 *
 * Includes breadcrumb navigation and a ChatBox at the bottom.
 */

import { useEffect } from 'react'
import { Allotment } from 'allotment'
import { ChevronRight, Sparkles } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import mermaid from 'mermaid'
import ChatBox from '../chat/ChatBox'
import RepoOverview from './RepoOverview'
import FileSummary from './FileSummary'
import LineExplanation from './LineExplanation'

type Tier = 'empty' | 'repo' | 'file' | 'line'

function getTier(repoId: string | null, currentFile: string | null,
                 selectedLine: number | null, selectedRange: { start: number; end: number } | null): Tier {
  if (selectedLine || selectedRange) return 'line'
  if (currentFile) return 'file'
  if (repoId) return 'repo'
  return 'empty'
}

export default function ContextPanel() {
  const {
    repoId, repoPath, currentFile, selectedLine, selectedRange,
    setSelectedLine, setSelectedRange, clearFile,
  } = useCodeStore()

  const tier = getTier(repoId, currentFile, selectedLine, selectedRange)

  // Initialize mermaid once
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false, theme: 'dark',
      themeVariables: {
        primaryColor: '#5b9cf5', primaryTextColor: '#e2e6f0', primaryBorderColor: '#252d3a',
        lineColor: '#8b949e', secondaryColor: '#12161e', tertiaryColor: '#0a0d12',
      },
    })
  }, [])

  const repoName = repoPath?.split(/[/\\]/).pop() || null
  const fileName = currentFile?.split(/[/\\]/).pop() || null
  const lineLabel = selectedRange
    ? `Lines ${selectedRange.start}-${selectedRange.end}`
    : selectedLine ? `Line ${selectedLine}` : null

  return (
    <div className="h-full flex flex-col bg-ct-bg">
      {/* Breadcrumb navigation */}
      {tier !== 'empty' && (
        <div className="flex-shrink-0 flex items-center gap-1 px-4 py-2 border-b border-ct-border text-xs bg-ct-surface">
          {repoName && (
            <button
              onClick={() => { clearFile(); setSelectedLine(null); setSelectedRange(null) }}
              className={`hover:text-ct-primary transition-colors ${tier === 'repo' ? 'text-ct-primary font-medium' : 'text-ct-text-secondary'}`}
            >
              {repoName}
            </button>
          )}
          {fileName && (
            <>
              <ChevronRight className="w-3 h-3 text-ct-text-secondary" />
              <button
                onClick={() => { setSelectedLine(null); setSelectedRange(null) }}
                className={`hover:text-ct-primary transition-colors truncate max-w-[200px] ${tier === 'file' ? 'text-ct-primary font-medium' : 'text-ct-text-secondary'}`}
              >
                {fileName}
              </button>
            </>
          )}
          {lineLabel && (
            <>
              <ChevronRight className="w-3 h-3 text-ct-text-secondary" />
              <span className="text-ct-warm font-medium">{lineLabel}</span>
            </>
          )}
        </div>
      )}

      {/* Content + Chat split */}
      <div className="flex-1 min-h-0">
        <Allotment vertical>
          <Allotment.Pane minSize={100} preferredSize="70%">
            {tier === 'empty' && (
              <div className="h-full flex items-center justify-center text-ct-text-secondary tier-enter">
                <div className="text-center space-y-3">
                  <Sparkles className="w-12 h-12 mx-auto text-ct-primary opacity-50" />
                  <p className="text-sm">Open a repository to get started</p>
                </div>
              </div>
            )}
            {tier === 'repo' && <RepoOverview />}
            {tier === 'file' && <FileSummary />}
            {tier === 'line' && <LineExplanation />}
          </Allotment.Pane>
          <Allotment.Pane minSize={48} preferredSize={200}>
            <ChatBox />
          </Allotment.Pane>
        </Allotment>
      </div>
    </div>
  )
}
