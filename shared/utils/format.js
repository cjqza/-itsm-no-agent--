/**
 * Time formatting utilities shared across all frontends.
 */
import dayjs from 'dayjs'

/**
 * Format a datetime string.
 * @param {string} t - ISO datetime string
 * @param {string} fmt - dayjs format string (default: 'YYYY-MM-DD HH:mm')
 * @returns {string}
 */
export function formatTime(t, fmt = 'YYYY-MM-DD HH:mm') {
  return t ? dayjs(t).format(fmt) : ''
}

/**
 * Format time as short datetime (MM-DD HH:mm).
 */
export function formatShortTime(t) {
  return t ? dayjs(t).format('MM-DD HH:mm') : ''
}

/**
 * Format time for chat messages (HH:mm).
 */
export function formatMsgTime(t) {
  return t ? dayjs(t).format('HH:mm') : ''
}
