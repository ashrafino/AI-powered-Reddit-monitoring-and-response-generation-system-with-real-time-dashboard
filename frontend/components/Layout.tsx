import Link from 'next/link'
import { ReactNode } from 'react'

export default function Layout({ children }: { children: ReactNode }) {
  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      window.location.href = '/'
    }
  }
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="font-semibold">RedditBot</div>
          <nav className="space-x-4 text-sm">
            <Link className="text-gray-700 hover:text-black" href="/dashboard">Dashboard</Link>
            <Link className="text-gray-700 hover:text-black" href="/configs">Configs</Link>
            <Link className="text-gray-700 hover:text-black" href="/clients">Clients</Link>
            <button onClick={logout} className="ml-2 px-3 py-1 rounded-md border">Logout</button>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  )
}
