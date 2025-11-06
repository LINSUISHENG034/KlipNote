import { describe, it, expect } from 'vitest'
import { formatTime } from '@/utils/formatters'

describe('formatTime', () => {
  it('should format 0 seconds as "00:00"', () => {
    expect(formatTime(0)).toBe('00:00')
  })

  it('should format 65 seconds as "01:05"', () => {
    expect(formatTime(65)).toBe('01:05')
  })

  it('should format 3661 seconds as "61:01" (over 1 hour)', () => {
    expect(formatTime(3661)).toBe('61:01')
  })

  it('should handle negative values by returning "00:00"', () => {
    expect(formatTime(-10)).toBe('00:00')
    expect(formatTime(-100)).toBe('00:00')
  })

  it('should handle decimal seconds by rounding down', () => {
    expect(formatTime(0.7)).toBe('00:00')
    expect(formatTime(65.5)).toBe('01:05')
    expect(formatTime(65.9)).toBe('01:05')
  })

  it('should handle 60 seconds as "01:00"', () => {
    expect(formatTime(60)).toBe('01:00')
  })

  it('should handle 59 seconds as "00:59"', () => {
    expect(formatTime(59)).toBe('00:59')
  })

  it('should handle large values correctly', () => {
    expect(formatTime(7200)).toBe('120:00') // 2 hours
    expect(formatTime(9999)).toBe('166:39')
  })

  it('should pad minutes and seconds with leading zeros', () => {
    expect(formatTime(1)).toBe('00:01')
    expect(formatTime(5)).toBe('00:05')
    expect(formatTime(61)).toBe('01:01')
  })
})
