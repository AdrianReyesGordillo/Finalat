/**
 * Utilidades de formateo de números.
 * Siempre usa punto como separador decimal y coma como separador de miles.
 * Ejemplo: 1234567.89 → "1,234,567.89"
 */

const LOCALE = 'en-US'

/**
 * Formatea un número como moneda con 2 decimales.
 * Ejemplo: 1234.5 → "1,234.50"
 */
export function formatMoney(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '0.00'
  return Number(value).toLocaleString(LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Formatea un número sin decimales (para cantidades enteras grandes).
 * Ejemplo: 1234567 → "1,234,567"
 */
export function formatNumber(value) {
  if (value === null || value === undefined || isNaN(value)) return '0'
  return Number(value).toLocaleString(LOCALE, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

/**
 * Formatea un porcentaje con 2 decimales.
 * Ejemplo: 16.9 → "16.90"
 */
export function formatPct(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '0.00'
  return Number(value).toLocaleString(LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}
