// API base URL configuration
// In development, this should point to the backend API
// In production with Docker, this should be set via environment variables

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';
