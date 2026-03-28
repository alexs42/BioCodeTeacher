import { Check, Loader2 } from 'lucide-react'

interface Phase {
  id: string
  label: string
  detail?: string | null
}

interface PhaseTrackerProps {
  phases: Phase[]
  currentPhase: string | null
  completedPhases: Set<string>
}

export function PhaseTracker({ phases, currentPhase, completedPhases }: PhaseTrackerProps) {
  return (
    <div className="flex items-center gap-0 px-4 py-3 overflow-x-auto text-xs">
      {phases.map((phase, i) => {
        const isCompleted = completedPhases.has(phase.id)
        const isCurrent = phase.id === currentPhase
        return (
          <div key={phase.id} className="flex items-center shrink-0">
            {/* Connector line */}
            {i > 0 && (
              <div className={`w-8 h-px transition-colors duration-500 ${
                isCompleted || isCurrent ? 'bg-ct-primary' : 'bg-ct-border'
              }`} />
            )}

            {/* Dot */}
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 transition-all duration-300 ${
              isCompleted
                ? 'bg-ct-accent/20 border-2 border-ct-accent'
                : isCurrent
                  ? 'bg-ct-primary/20 border-2 border-ct-primary phase-active'
                  : 'bg-ct-surface border-2 border-ct-border'
            }`}>
              {isCompleted && <Check size={12} className="text-ct-accent" />}
              {isCurrent && <Loader2 size={12} className="text-ct-primary animate-spin" />}
            </div>

            {/* Label */}
            <span className={`ml-1.5 mr-1 whitespace-nowrap transition-colors ${
              isCompleted ? 'text-ct-accent' :
              isCurrent ? 'text-ct-primary font-medium' :
              'text-ct-text-secondary'
            }`}>
              {phase.label}
            </span>
          </div>
        )
      })}
    </div>
  )
}
