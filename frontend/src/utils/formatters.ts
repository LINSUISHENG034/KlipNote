/**
 * Convert float seconds to MM:SS format
 * @param seconds - Float seconds (e.g., 65.5)
 * @returns Formatted time string (e.g., "01:05")
 */
export function formatTime(seconds: number): string {
  if (seconds < 0) return "00:00"

  const totalSeconds = Math.floor(seconds)
  const minutes = Math.floor(totalSeconds / 60)
  const remainingSeconds = totalSeconds % 60

  const mm = String(minutes).padStart(2, '0')
  const ss = String(remainingSeconds).padStart(2, '0')

  return `${mm}:${ss}`
}
