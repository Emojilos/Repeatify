import { HashRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Topics from './pages/Topics'
import TopicDetail from './pages/TopicDetail'
import TopicFire from './pages/TopicFire'
import Practice from './pages/Practice'
import PracticeSession from './pages/PracticeSession'
import PracticeResults from './pages/PracticeResults'
import Progress from './pages/Progress'
import Profile from './pages/Profile'

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/topics" element={<Topics />} />
        <Route path="/topics/:id" element={<TopicDetail />} />
        <Route path="/topics/:id/fire" element={<TopicFire />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/practice/session" element={<PracticeSession />} />
        <Route path="/practice/results" element={<PracticeResults />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </HashRouter>
  )
}

export default App
