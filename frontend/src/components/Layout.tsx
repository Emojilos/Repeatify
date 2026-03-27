import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import XpPopup from './XpPopup'
import LevelUpModal from './LevelUpModal'
import ErrorBoundary from './ErrorBoundary'
import FormulaSheet from './FormulaSheet'

export default function Layout() {
  return (
    <div className="flex h-screen flex-col bg-white print:h-auto print:overflow-visible dark:bg-gray-900">
      <Header />
      <XpPopup />
      <LevelUpModal />
      <FormulaSheet />
      <div className="flex flex-1 overflow-hidden print:overflow-visible">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6 print:overflow-visible print:p-0 dark:bg-gray-900">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
