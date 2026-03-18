const SHANGHAI_TIMEZONE = 'Asia/Shanghai'
const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000

const shanghaiDateTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: SHANGHAI_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

const shanghaiTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: SHANGHAI_TIMEZONE,
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

const shanghaiMonthDayFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: SHANGHAI_TIMEZONE,
  month: '2-digit',
  day: '2-digit',
})

function toDate(value) {
  if (value instanceof Date) return value
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date
}

function getParts(value) {
  const date = toDate(value)
  if (!date) return null

  const parts = {}
  for (const part of shanghaiDateTimeFormatter.formatToParts(date)) {
    if (part.type !== 'literal') {
      parts[part.type] = part.value
    }
  }
  return parts
}

export function formatShanghaiDateTime(value) {
  const date = toDate(value)
  if (!date) return ''
  return shanghaiDateTimeFormatter.format(date)
}

export function formatShanghaiTime(value) {
  const date = toDate(value)
  if (!date) return ''
  return shanghaiTimeFormatter.format(date)
}

export function formatShanghaiMonthDay(value) {
  const date = toDate(value)
  if (!date) return ''
  return shanghaiMonthDayFormatter.format(date)
}

export function formatShanghaiMonthDayTime(value) {
  const parts = getParts(value)
  if (!parts) return ''
  return `${Number(parts.month)}/${Number(parts.day)} ${parts.hour}:${parts.minute}`
}

export function formatShanghaiChatTimestamp(value) {
  const parts = getParts(value)
  if (!parts) return ''

  const hourNumber = Number(parts.hour)
  const period = hourNumber < 12 ? '上午' : '下午'
  return `${Number(parts.month)}/${Number(parts.day)} ${period} ${parts.hour}:${parts.minute}`
}

export function getShanghaiHour(value = new Date()) {
  const parts = getParts(value)
  return parts ? Number(parts.hour) : 0
}

export function getShanghaiDateStamp(value = new Date()) {
  const parts = getParts(value)
  if (!parts) return ''
  return `${parts.year}-${parts.month}-${parts.day}`
}

export function getShanghaiDayNumber(value) {
  const date = toDate(value)
  if (!date) return 0
  return Math.floor((date.getTime() + SHANGHAI_OFFSET_MS) / 86400000)
}

export function getShanghaiIsoTimestamp(value = new Date()) {
  const parts = getParts(value)
  if (!parts) return ''
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}+08:00`
}
