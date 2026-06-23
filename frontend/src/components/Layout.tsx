import { ReactNode } from 'react'
import Navbar from './Navbar'
import Footer from './Footer'

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">{children}</main>
      <Footer />
      <style>{`
        .layout { display: flex; flex-direction: column; min-height: 100vh; }
        .main-content { flex: 1; display: flex; flex-direction: column; }
      `}</style>
    </div>
  )
}
