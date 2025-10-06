// Runtime configuration that adapts to any environment
// This ensures the app works on any IP/domain without hardcoding

export function getApiBaseUrl(): string {
  // Only run in browser
  if (typeof window === 'undefined') {
    return ''; // SSR uses relative URLs
  }

  const hostname = window.location.hostname;
  
  // Check if there's a build-time override
  const buildTimeBase = process.env.NEXT_PUBLIC_API_BASE;
  if (buildTimeBase && buildTimeBase.trim() !== '') {
    console.log('Using build-time API base:', buildTimeBase);
    return buildTimeBase;
  }
  
  // Development environment (localhost)
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.log('Development mode: using localhost:8001');
    return 'http://localhost:8001';
  }
  
  // Production: use relative URLs
  // Nginx will proxy /api/* to the backend service
  console.log('Production mode: using relative URLs (nginx proxy)');
  return '';
}

// Log the detected configuration on module load (browser only)
if (typeof window !== 'undefined') {
  console.log('API Base URL detected:', getApiBaseUrl() || '(relative URLs)');
  console.log('Current hostname:', window.location.hostname);
}
