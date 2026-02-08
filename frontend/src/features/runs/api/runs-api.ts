export type RunResponse = {
  runId: string
  status: string
  startedAt: string
  endedAt: string | null
  statusReason: string | null
}

type ApiProblem = {
  title?: string
  detail?: string
  errorCode?: string
  status?: number
}

export class ApiError extends Error {
  problem?: ApiProblem

  constructor(message: string, problem?: ApiProblem) {
    super(message)
    this.problem = problem
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080/api').replace(/\/$/, '')
const baseUrl = `${API_BASE_URL}/runs`

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

export const triggerRun = async (): Promise<RunResponse> => {
  const response = await fetch(baseUrl, {
    method: 'POST',
  })
  return handleResponse<RunResponse>(response)
}

export const getRun = async (runId: string): Promise<RunResponse> => {
  const response = await fetch(`${baseUrl}/${encodeURIComponent(runId)}`)
  return handleResponse<RunResponse>(response)
}
