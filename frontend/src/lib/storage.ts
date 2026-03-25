const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SUPABASE_STORAGE_RE = /^https:\/\/[^/]+\.supabase\.co\/storage\/v1\/object\/public\/(.+)$/

/**
 * Rewrite a Supabase Storage URL to go through our backend proxy,
 * avoiding third-party cookie/storage blocking in browsers like Firefox.
 */
export function proxyImageUrl(url: string): string {
  const match = url.match(SUPABASE_STORAGE_RE)
  if (match) {
    return `${API_URL}/api/storage/${match[1]}`
  }
  return url
}
