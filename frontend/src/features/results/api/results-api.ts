export type ResultsView = 'today' | 'all-time'

export type ResultRecord = {
  id: number
  runId: string
  queryId: string | null
  queryText: string | null
  searchQuery: string | null
  domain: string | null
  title: string | null
  snippet: string | null
  rawUrl: string | null
  finalUrl: string | null
  createdAt: string | null
  rawHtmlPath: string | null
  visibleText: string | null
  cacheKey: string | null
  cachedAt: string | null
  lastSeenAt: string | null
  normalizedUrl: string | null
  canonicalId: number | null
  isDuplicate: boolean
  isHidden: boolean
  duplicateCount: number
  relevanceScore: number | null
  scoredAt: string | null
  scoreVersion: string | null
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
const baseUrl = `${API_BASE_URL}/results`

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

type GetResultsParams = {
  view?: ResultsView
  includeHidden?: boolean
  runId?: string
}

export const getResults = async ({ view = 'today', includeHidden = false, runId }: GetResultsParams) => {
  const params = new URLSearchParams()
  if (runId) {
    params.set('runId', runId)
  }
  params.set('view', view)
  if (includeHidden) {
    params.set('includeHidden', 'true')
  }

  const response = await fetch(`${baseUrl}?${params.toString()}`)
  return handleResponse<ResultRecord[]>(response)
}
