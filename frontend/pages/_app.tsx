import type { AppProps } from 'next/app'
import Head from 'next/head'
import '../styles/globals.css'
import { AuthProvider } from '../utils/authContext'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { AuthDebugTrigger } from '../components/AuthDebugPanel'

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <link rel="icon" href="/favicon.svg" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <ErrorBoundary>
        <AuthProvider>
          <Component {...pageProps} />
          <AuthDebugTrigger />
        </AuthProvider>
      </ErrorBoundary>
    </>
  )
}
