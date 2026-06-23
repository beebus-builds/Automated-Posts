import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Vault from './pages/Vault'
import Community from './pages/Community'
import Guidelines from './pages/Guidelines'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/vault" element={<Vault />} />
        <Route path="/community" element={<Community />} />
        <Route path="/guidelines" element={<Guidelines />} />
      </Routes>
    </Layout>
  )
}
