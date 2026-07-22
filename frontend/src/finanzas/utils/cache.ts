/**
 * API Cache Utility for Finanzas Module
 *
 * Provides localStorage-based caching for API GET requests.
 * Cache is automatically invalidated when the user performs mutations
 * (POST, PUT, DELETE) on related endpoints.
 *
 * Usage in views:
 *   import { cachedGet, invalidateCache } from '../utils/cache'
 *
 *   // Instead of: const res = await finApi.get('/api/deudas')
 *   // Use:        const res = await cachedGet('/api/deudas')
 *
 *   // After a mutation, invalidate related cache:
 *   await finApi.post('/api/deudas', payload)
 *   invalidateCache('/api/deudas')
 */

import finApi from './api'

const CACHE_PREFIX = 'fin_cache_'
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes max staleness

interface CacheEntry {
  data: any
  timestamp: number
}

/**
 * Generate a storage key from the endpoint URL.
 */
function cacheKey(url: string): string {
  return CACHE_PREFIX + url.replace(/[^a-zA-Z0-9/_-]/g, '_')
}

/**
 * Read from localStorage cache.
 * Returns null if not found or expired.
 */
function readCache(url: string): any | null {
  try {
    const raw = localStorage.getItem(cacheKey(url))
    if (!raw) return null
    const entry: CacheEntry = JSON.parse(raw)
    const age = Date.now() - entry.timestamp
    if (age > CACHE_TTL) {
      localStorage.removeItem(cacheKey(url))
      return null
    }
    return entry.data
  } catch {
    return null
  }
}

/**
 * Write to localStorage cache.
 */
function writeCache(url: string, data: any): void {
  try {
    const entry: CacheEntry = { data, timestamp: Date.now() }
    localStorage.setItem(cacheKey(url), JSON.stringify(entry))
  } catch {
    // Storage full or unavailable — silently skip
  }
}

/**
 * Invalidate (remove) cache for a specific endpoint or all endpoints
 * that start with the given prefix.
 *
 * Examples:
 *   invalidateCache('/api/deudas')        → removes exact match
 *   invalidateCache('/api/inversiones')    → removes /api/inversiones and /api/inversiones/*
 *   invalidateCache()                      → clears ALL finanzas cache
 */
export function invalidateCache(urlPrefix?: string): void {
  if (!urlPrefix) {
    // Clear all finanzas cache
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(CACHE_PREFIX)) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k))
    return
  }

  const prefix = cacheKey(urlPrefix)
  const keysToRemove: string[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(prefix)) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

/**
 * Perform a GET request with localStorage caching.
 *
 * - If cached data exists and is fresh (< TTL), returns it immediately
 *   without making a network request.
 * - If no cache or expired, fetches from network and caches the result.
 *
 * Returns an axios-like response object: { data: ... }
 */
export async function cachedGet(url: string, options?: { forceRefresh?: boolean; params?: Record<string, any> }): Promise<{ data: any }> {
  // Build full cache key including params
  let fullUrl = url
  if (options?.params) {
    const paramStr = Object.entries(options.params)
      .filter(([_, v]) => v !== undefined && v !== null)
      .map(([k, v]) => `${k}=${v}`)
      .sort()
      .join('&')
    if (paramStr) fullUrl = `${url}?${paramStr}`
  }

  // Check cache first (unless forced refresh)
  if (!options?.forceRefresh) {
    const cached = readCache(fullUrl)
    if (cached !== null) {
      return { data: cached }
    }
  }

  // Fetch from network
  const response = await finApi.get(url, options?.params ? { params: options.params } : undefined)
  writeCache(fullUrl, response.data)
  return response
}

/**
 * Mapping of mutation endpoints to cache keys that should be invalidated.
 * When a POST/PUT/DELETE hits a URL, we invalidate all related caches.
 */
const INVALIDATION_MAP: Record<string, string[]> = {
  // Deudas
  '/api/deudas': ['/api/deudas', '/api/dashboard'],

  // Créditos
  '/api/creditos': ['/api/creditos', '/api/dashboard'],
  '/api/creditos/update-card': ['/api/creditos', '/api/dashboard'],

  // Gastos/Ingresos
  '/api/gi/records': ['/api/gi/records', '/api/dashboard', '/api/patrimonio'],
  '/api/gi/categories': ['/api/gi/categories'],

  // Inversiones
  '/api/inversiones': ['/api/inversiones', '/api/dashboard'],
  '/api/inversiones/update-balances': ['/api/inversiones', '/api/dashboard'],
  '/api/inversiones/mark-updated': ['/api/inversiones'],
  '/api/inversiones/afore/update-data': ['/api/inversiones', '/api/dashboard'],
  '/api/inversiones/prestamos': ['/api/inversiones', '/api/dashboard'],
  '/api/inversiones/prestamos/update-data': ['/api/inversiones', '/api/dashboard'],

  // GBM
  '/api/gbm/upload': ['/api/gbm', '/api/dashboard'],
  '/api/gbm/portfolio': ['/api/gbm', '/api/dashboard'],

  // Aportaciones
  '/api/aportaciones': ['/api/aportaciones'],
  '/api/aportaciones/update-status': ['/api/aportaciones'],

  // Configuración (affects multiple views)
  '/api/config/ahorro': ['/api/config/ahorro', '/api/inversiones', '/api/dashboard'],
  '/api/config/creditos': ['/api/config/creditos', '/api/creditos', '/api/dashboard'],
  '/api/config/aportaciones': ['/api/config/aportaciones', '/api/aportaciones'],

  // Patrimonio
  '/api/patrimonio': ['/api/patrimonio', '/api/dashboard'],
}

/**
 * Auto-invalidation interceptor for finApi.
 * Attaches to response interceptor — after any successful POST/PUT/DELETE,
 * automatically invalidates related caches.
 */
finApi.interceptors.response.use((response) => {
  const method = response.config.method?.toLowerCase()
  if (method && ['post', 'put', 'delete', 'patch'].includes(method)) {
    const url = response.config.url || ''

    // Try exact match first
    const targets = INVALIDATION_MAP[url]
    if (targets) {
      targets.forEach(t => invalidateCache(t))
    } else {
      // Fallback: invalidate by base path (e.g., /api/gi/records/123 → /api/gi/records)
      const basePath = url.replace(/\/\d+$/, '')
      const baseTargets = INVALIDATION_MAP[basePath]
      if (baseTargets) {
        baseTargets.forEach(t => invalidateCache(t))
      }
    }

    // Always invalidate dashboard on any mutation (it aggregates everything)
    invalidateCache('/api/dashboard')
  }
  return response
})

export default { cachedGet, invalidateCache }
