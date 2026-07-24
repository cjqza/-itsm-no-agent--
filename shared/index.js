/**
 * Shared layer – single entry point.
 * Re-exports everything so consumers can do:
 *   import { statusType, formatTime, createApiClient } from '@shared'
 */
export { statusType, statusTagType, statusText, priorityType, slaColor, slaText, slaTagType } from './utils/status'
export { formatTime, formatShortTime, formatMsgTime } from './utils/format'
export { createApiClient } from './api/request'
