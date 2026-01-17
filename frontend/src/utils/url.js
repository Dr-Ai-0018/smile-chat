import { API_ORIGIN } from '../api/client'

const ABSOLUTE_URL_REGEX = /^(?:[a-z]+:)?\/\//i

export const resolveStaticUrl = (path) => {
  if (!path) return ''
  if (ABSOLUTE_URL_REGEX.test(path) || path.startsWith('data:')) {
    return path
  }
  try {
    return new URL(path, API_ORIGIN).toString()
  } catch {
    return path
  }
}
