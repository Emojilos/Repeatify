import { HashRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import OnboardingGuard from './components/OnboardingGuard'
import ToastContainer from './components/ToastContainer'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Topics from './pages/Topics'
import TopicDetail from './pages/TopicDetail'
import TopicPractice from './pages/TopicPractice'
import Practice from './pages/Practice'
import PracticeSession from './pages/PracticeSession'
import PracticeResults from './pages/PracticeResults'
import Progress from './pages/Progress'
import Profile from './pages/Profile'
import Onboarding from './pages/Onboarding'
import StudyPlan from './pages/StudyPlan'
import PrototypeDetail from './pages/PrototypeDetail'
import PrintProblems from './pages/PrintProblems'

function App() {
  return (
    <HashRouter>
      <ToastContainer />
      <Routes>
        {/* Public routes — no layout */}
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />

        {/* Protected routes — with onboarding guard */}
        <Route element={<ProtectedRoute />}>
          <Route element={<OnboardingGuard />}>
            {/* Standalone flows (no sidebar/header) */}
            <Route path="/onboarding" element={<Onboarding />} />
            {/* Main app with layout */}
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/topics" element={<Topics />} />
              <Route path="/topics/:id" element={<TopicDetail />} />
              <Route path="/topics/:id/practice" element={<TopicPractice />} />
              <Route path="/practice" element={<Practice />} />
              <Route path="/practice/session" element={<PracticeSession />} />
              <Route path="/practice/results" element={<PracticeResults />} />
              <Route path="/plan" element={<StudyPlan />} />
              <Route path="/progress" element={<Progress />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/prototypes/:id" element={<PrototypeDetail />} />
              <Route path="/print" element={<PrintProblems />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </HashRouter>
  )
}

export default App
