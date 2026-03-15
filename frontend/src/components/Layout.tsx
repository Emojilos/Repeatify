import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import XpPopup from './XpPopup'
import LevelUpModal from './LevelUpModal'
import ErrorBoundary from './ErrorBoundary'

export default function Layout() {
  return (
    <div className="flex h-screen flex-col">
      <Header />
      <XpPopup />
      <LevelUpModal />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
