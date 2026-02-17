export type Query = {
  id: string
  text: string
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export type QueryUpdate = {
  text?: string
  enabled?: boolean
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:18080/api').replace(/\/$/, '')

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const payload = await response.json()
      if (payload?.detail) {
        message = payload.detail
      } else if (payload?.title) {
        message = payload.title
      }
    } catch {
      if (response.statusText) {
        message = response.statusText
      }
    }
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const getQueries = () => request<Query[]>('/queries')

export const createQuery = (text: string) =>
  request<Query>('/queries', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })

export const updateQuery = (id: string, update: QueryUpdate) =>
  request<Query>(`/queries/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
