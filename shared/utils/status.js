/**
 * Status / priority / SLA mapping utilities shared across all frontends.
 */

// 工单状态 → Element Plus tag type
export function statusType(s) {
  return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success', closed: 'info' }[s] || 'info'
}

// alias: some components use statusTagType
export const statusTagType = statusType

// 工单状态 → 中文文本
export function statusText(s) {
  return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决', closed: '已关闭' }[s] || s
}

// 优先级 → Element Plus tag type
export function priorityType(p) {
  return { P1: 'danger', P2: 'warning', P3: '', P4: 'info' }[p] || ''
}

// SLA 状态 → 颜色值
export function slaColor(s) {
  return { green: '#67c23a', yellow: '#e6a23c', red: '#f56c6c', black: '#333' }[s] || '#999'
}

// SLA 状态 → 中文文本
export function slaText(s) {
  return { green: '正常', yellow: '预警', red: '警告', black: '超时' }[s] || ''
}

// SLA 状态 → Element Plus tag type
export function slaTagType(s) {
  return { green: 'success', yellow: 'warning', red: 'danger', black: 'info' }[s] || 'info'
}

// SLA 百分比 → 颜色值（0-50绿，50-80黄，80-100红，100+黑）
export function slaColorByPercent(percent) {
  if (percent >= 100) return '#333'
  if (percent >= 80) return '#f56c6c'
  if (percent >= 50) return '#e6a23c'
  return '#67c23a'
}
