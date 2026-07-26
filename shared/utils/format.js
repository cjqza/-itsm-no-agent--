/**
 * Time formatting utilities shared across all frontends.
 *
 * 后端存储 UTC 时间，前端显示时自动转换为本地时间。
 * timestamp 格式："2026-07-25T10:54:21.177894"（无时区后缀，视为 UTC）
 */
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)

/**
 * 将 UTC 时间戳转为本地时间格式化。
 * 如果 timestamp 已含时区信息（Z/+xx:xx），直接用；
 * 否则追加 'Z' 视为 UTC，dayjs 自动转本地时间显示。
 */
function toLocal(t) {
  if (!t) return null
  // 已有时区后缀 → 直接用
  if (typeof t === 'string' && (t.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(t))) {
    return dayjs(t)
  }
  // 无时区 → 视为 UTC，追加 Z
  return dayjs.utc(t).local()
}

/**
 * Format a datetime string.
 * @param {string} t - ISO datetime string (UTC)
 * @param {string} fmt - dayjs format string (default: 'YYYY-MM-DD HH:mm')
 * @returns {string}
 */
export function formatTime(t, fmt = 'YYYY-MM-DD HH:mm') {
  const d = toLocal(t)
  return d ? d.format(fmt) : ''
}

/**
 * Format time as short datetime (MM-DD HH:mm).
 */
export function formatShortTime(t) {
  const d = toLocal(t)
  return d ? d.format('MM-DD HH:mm') : ''
}

/**
 * Format time for chat messages (HH:mm).
 */
export function formatMsgTime(t) {
  const d = toLocal(t)
  return d ? d.format('HH:mm') : ''
}

/**
 * 将 UTC 时间戳转为 Date 对象（无时区后缀视为 UTC）。
 * 用于 SLA 等需要原生 Date 做差值计算的场景。
 * @param {string} t - ISO datetime string
 * @returns {Date}
 */
export function utcToDate(t) {
  if (!t) return new Date()
  return new Date(
    typeof t === 'string' && !t.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(t) ? t + 'Z' : t
  )
}
