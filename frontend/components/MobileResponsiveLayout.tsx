import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useWebSocket } from './WebSocketProvider'

interface MobileResponsiveLayoutProps {
  children: React.ReactNode
}

const MobileResponsiveLayout: React.FC<MobileResponsiveLayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const { isConnected, connectionHealth } = useWebSocket()

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      window.location.href = '/'
    }
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-4">
              <div className="font-semibold text-lg">RedditBot</div>
              
              {/* WebSocket status hidden - not used in production */}
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <Link 
                className="text-gray-700 hover:text-black transition-colors" 
                href="/dashboard"
              >
                Dashboard
              </Link>
              <Link 
                className="text-gray-700 hover:text-black transition-colors" 
                href="/configs"
              >
                Configs
              </Link>
              <Link 
                className="text-gray-700 hover:text-black transition-colors" 
                href="/clients"
              >
                Clients
              </Link>
              <button 
                onClick={logout} 
                className="px-3 py-1 rounded-md border hover:bg-gray-50 transition-colors"
              >
                Logout
              </button>
            </nav>

            {/* Mobile Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-md hover:bg-gray-100 transition-colors"
              aria-label="Toggle mobile menu"
            >
              <svg 
                className="w-6 h-6" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M6 18L18 6M6 6l12 12" 
                  />
                ) : (
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M4 6h16M4 12h16M4 18h16" 
                  />
                )}
              </svg>
            </button>
          </div>

          {/* Mobile Navigation Menu */}
          {isMobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 border-t">
              <nav className="flex flex-col space-y-3 pt-4">
                <Link 
                  className="text-gray-700 hover:text-black transition-colors py-2" 
                  href="/dashboard"
                  onClick={closeMobileMenu}
                >
                  Dashboard
                </Link>
                <Link 
                  className="text-gray-700 hover:text-black transition-colors py-2" 
                  href="/configs"
                  onClick={closeMobileMenu}
                >
                  Configs
                </Link>
                <Link 
                  className="text-gray-700 hover:text-black transition-colors py-2" 
                  href="/clients"
                  onClick={closeMobileMenu}
                >
                  Clients
                </Link>
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600">Connection Status</span>
                    {/* WebSocket status hidden - not used in production */}
                  </div>
                  {connectionHealth?.latency_ms && (
                    <div className="text-xs text-gray-500 py-1">
                      Latency: {connectionHealth.latency_ms}ms
                    </div>
                  )}
                </div>
                <button 
                  onClick={() => { logout(); closeMobileMenu(); }} 
                  className="text-left text-red-600 hover:text-red-800 transition-colors py-2"
                >
                  Logout
                </button>
              </nav>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Mobile-specific content adjustments */}
        <div className={`${isMobile ? 'space-y-4' : 'space-y-6'}`}>
          {children}
        </div>
      </main>

      {/* Mobile Bottom Navigation (Optional) */}
      {isMobile && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t z-40">
          <div className="flex items-center justify-around py-2">
            <Link 
              href="/dashboard" 
              className="flex flex-col items-center py-2 px-4 text-gray-600 hover:text-black transition-colors"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
              </svg>
              <span className="text-xs">Dashboard</span>
            </Link>
            
            <Link 
              href="/configs" 
              className="flex flex-col items-center py-2 px-4 text-gray-600 hover:text-black transition-colors"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-xs">Settings</span>
            </Link>
            
            <button 
              onClick={() => setIsMobileMenuOpen(true)}
              className="flex flex-col items-center py-2 px-4 text-gray-600 hover:text-black transition-colors"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <span className="text-xs">Menu</span>
            </button>
          </div>
        </div>
      )}

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && isMobile && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={closeMobileMenu}
        />
      )}

      {/* Add bottom padding for mobile navigation */}
      {isMobile && <div className="h-16"></div>}
    </div>
  )
}

export default MobileResponsiveLayout