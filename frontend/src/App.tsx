import { useEffect } from 'react'
import { Allotment } from 'allotment'
import 'allotment/dist/style.css'
import { useCodeStore } from './store/codeStore'
import Header from './components/layout/Header'
import CodePanel from './components/code/CodePanel'
import ContextPanel from './components/context/ContextPanel'
import SetupModal from './components/setup/SetupModal'
import SettingsModal from './components/settings/SettingsModal'
import './styles/theme.css'

function App() {
  const { isDarkMode, apiKey, showSetupModal, showSettingsModal, setShowSetupModal, setShowSettingsModal } = useCodeStore()

  // Apply dark/light mode class to document
  useEffect(() => {
    document.documentElement.classList.toggle('light', !isDarkMode)
  }, [isDarkMode])

  // Show setup modal if no API key
  useEffect(() => {
    if (!apiKey) {
      setShowSetupModal(true)
    }
  }, [apiKey, setShowSetupModal])

  return (
    <div className="h-screen flex flex-col bg-ct-bg text-ct-text overflow-hidden">
      <Header />

      <div className="flex-1 overflow-hidden">
        <Allotment>
          <Allotment.Pane minSize={300}>
            <CodePanel />
          </Allotment.Pane>
          <Allotment.Pane minSize={300}>
            <ContextPanel />
          </Allotment.Pane>
        </Allotment>
      </div>

      {showSetupModal && <SetupModal />}
      <SettingsModal isOpen={showSettingsModal} onClose={() => setShowSettingsModal(false)} />
    </div>
  )
}

export default App
