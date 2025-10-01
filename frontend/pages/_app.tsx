import type { AppProps } from 'next/app'
import Head from 'next/head'
import { useEffect, useState } from 'react'
import '../styles/globals.css'

export default function MyApp({ Component, pageProps }: AppProps) {
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Optimize: Check if we're in browser before accessing localStorage
    if (typeof window !== 'undefined') {
      setToken(localStorage.getItem('token'))
    }
    setIsLoading(false)
  }, [])

  // Show loading state to prevent hydration mismatch
  if (isLoading) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>
  }

  return (
    <>
      <Head>
        <link rel="icon" href="/favicon.svg" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {...pageProps} token={token} setToken={setToken} />
    </>
  )
}
