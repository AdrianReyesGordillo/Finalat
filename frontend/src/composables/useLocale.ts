/**
 * useLocale — Composable for es-MX locale formatting (dates, numbers).
 * Centralizes all locale-dependent formatting for consistency across the SPA.
 */

const LOCALE = 'es-MX'

const shortDateFormatter = new Intl.DateTimeFormat(LOCALE, {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

const longDateFormatter = new Intl.DateTimeFormat(LOCALE, {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

const dateTimeFormatter = new Intl.DateTimeFormat(LOCALE, {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const currencyFormatter = new Intl.NumberFormat(LOCALE, {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const percentFormatter = new Intl.NumberFormat(LOCALE, {
  style: 'percent',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function useLocale() {
  /**
   * Format a date string or Date object in short es-MX format (dd/mm/yyyy).
   */
  function formatDate(value: string | Date | null | undefined): string {
    if (!value) return '—'
    const date = typeof value === 'string' ? new Date(value.includes('T') ? value : value + 'T00:00:00') : value
    if (isNaN(date.getTime())) return '—'
    return shortDateFormatter.format(date)
  }

  /**
   * Format a date string or Date object in long es-MX format (e.g., "5 de enero de 2024").
   */
  function formatDateLong(value: string | Date | null | undefined): string {
    if (!value) return '—'
    const date = typeof value === 'string' ? new Date(value.includes('T') ? value : value + 'T00:00:00') : value
    if (isNaN(date.getTime())) return '—'
    return longDateFormatter.format(date)
  }

  /**
   * Format a date string or Date object with time in es-MX format.
   */
  function formatDateTime(value: string | Date | null | undefined): string {
    if (!value) return '—'
    const date = typeof value === 'string' ? new Date(value) : value
    if (isNaN(date.getTime())) return '—'
    return dateTimeFormatter.format(date)
  }

  /**
   * Format a number as MXN currency (es-MX).
   */
  function formatCurrency(value: number | null | undefined): string {
    if (value == null || isNaN(value)) return '—'
    return currencyFormatter.format(value)
  }

  /**
   * Format a number as percentage (es-MX).
   * Input: 0.155 → "15.50%"
   */
  function formatPercent(value: number | null | undefined): string {
    if (value == null || isNaN(value)) return '—'
    return percentFormatter.format(value)
  }

  /**
   * Format a decimal percentage directly (e.g., 15.5 → "15.50%").
   * Use when value is already a percentage number, not a fraction.
   */
  function formatPercentDirect(value: number | null | undefined): string {
    if (value == null || isNaN(value)) return '—'
    return `${value.toFixed(2)}%`
  }

  return {
    locale: LOCALE,
    formatDate,
    formatDateLong,
    formatDateTime,
    formatCurrency,
    formatPercent,
    formatPercentDirect,
  }
}
