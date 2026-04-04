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
    <div className="flex h-screen flex-col bg-white dark:bg-gray-900 print:block print:h-auto">
      <div className="print:hidden">
        <Header />
        <XpPopup />
        <LevelUpModal />
        <FormulaSheetButton />
      </div>
      <div className="flex flex-1 overflow-hidden print:block print:overflow-visible">
        <div className="print:hidden">
          <Sidebar />
        </div>
        <main className="min-w-0 flex-1 overflow-y-auto bg-gray-50 p-6 dark:bg-gray-900 print:bg-white print:p-0 print:overflow-visible">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
        <div className="print:hidden">
          <FormulaSheet />
        </div>
      </div>
    </div>
  )
}
