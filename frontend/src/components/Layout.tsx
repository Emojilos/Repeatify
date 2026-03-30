import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import XpPopup from './XpPopup'
import LevelUpModal from './LevelUpModal'
import ErrorBoundary from './ErrorBoundary'
import FormulaSheet from './FormulaSheet'
import FormulaSheetButton from './FormulaSheetButton'

export default function Layout() {
  return (
    <div className="flex h-screen flex-col bg-white dark:bg-gray-900">
      <Header />
      <XpPopup />
      <LevelUpModal />
      <FormulaSheetButton />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-y-auto bg-gray-50 p-6 dark:bg-gray-900">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
        <FormulaSheet />
      </div>
    </div>
  )
}
