const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SUPABASE_STORAGE_RE = /^https:\/\/[^/]+\.supabase\.co\/storage\/v1\/object\/public\/(.+)$/
const LOCAL_SHKOLKOVO_IMAGE_RE = /^data\/raw\/shkolkovo\/images\/(.+)$/

/**
 * Rewrite a Supabase Storage URL to go through our backend proxy,
 * avoiding third-party cookie/storage blocking in browsers like Firefox.
 */
export function proxyImageUrl(url: string): string {
  const trimmed = url.trim()

  const localMatch = trimmed.match(LOCAL_SHKOLKOVO_IMAGE_RE)
  if (localMatch) {
    return `${API_URL}/api/storage/raw-shkolkovo/${encodePath(localMatch[1])}`
  }

  const storageMatch = trimmed.match(SUPABASE_STORAGE_RE)
  if (storageMatch) {
    return `${API_URL}/api/storage/${storageMatch[1]}`
  }
  return trimmed
}

function encodePath(path: string): string {
  return path.split('/').map(encodeURIComponent).join('/')
}
