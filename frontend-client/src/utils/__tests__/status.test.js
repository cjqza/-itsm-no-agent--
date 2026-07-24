import { describe, it, expect } from 'vitest'
import { statusType, statusText } from '@shared/utils/status'

describe('status utils', () => {
  it('statusType returns correct types', () => {
    expect(statusType('pending')).toBe('info')
    expect(statusType('processing')).toBe('warning')
    expect(statusType('resolved')).toBe('success')
  })
  it('statusText returns correct text', () => {
    expect(statusText('pending')).toBe('待接单')
    expect(statusText('resolved')).toBe('已解决')
  })
})
