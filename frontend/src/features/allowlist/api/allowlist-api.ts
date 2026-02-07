export type AllowlistEntry = {
  domain: string
  enabled: boolean
}

export type AllowlistUpdate = {
  domain?: string
  enabled?: boolean
}

type ApiProblem = {
  title?: string
  detail?: string
  errorCode?: string
  status?: number
}

class ApiError extends Error {
  problem?: ApiProblem

  constructor(message: string, problem?: ApiProblem) {
    super(message)
    this.problem = problem
  }
}

const baseUrl = '/api/allowlists'

const parseProblem = async (response: Response): Promise<ApiProblem | undefined> => {
  try {
    return (await response.json()) as ApiProblem
  } catch {
    return undefined
  }
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const problem = await parseProblem(response)
    const message = problem?.detail || problem?.title || 'Request failed'
    throw new ApiError(message, problem)
  }

  return (await response.json()) as T
}

export const fetchAllowlists = async (): Promise<AllowlistEntry[]> => {
  const response = await fetch(baseUrl)
  return handleResponse<AllowlistEntry[]>(response)
}

export const createAllowlist = async (domain: string): Promise<AllowlistEntry> => {
  const response = await fetch(baseUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain }),
  })
  return handleResponse<AllowlistEntry>(response)
}

export const updateAllowlist = async (
  currentDomain: string,
  update: AllowlistUpdate,
): Promise<AllowlistEntry> => {
  const response = await fetch(`${baseUrl}/${encodeURIComponent(currentDomain)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
  return handleResponse<AllowlistEntry>(response)
}

export { ApiError }
