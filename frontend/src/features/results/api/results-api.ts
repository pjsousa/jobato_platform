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

export type ResultDisplayRecord = Omit<ResultRecord, 'title' | 'snippet'> & {
  title: string
  company: string
  snippet: string
  source: string
  postedDate: string
  sourceUrl: string | null
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

const UNKNOWN_COMPANY = 'Unknown company'
const UNKNOWN_SOURCE = 'Unknown source'
const UNKNOWN_POSTED_DATE = 'Unknown date'

const normalizeText = (value: string | null | undefined) => {
  if (!value) {
    return ''
  }
  return value.trim()
}

const toTitleCase = (value: string) =>
  value
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1).toLowerCase()}`)
    .join(' ')

const normalizeDomain = (domain: string | null) => {
  const normalized = normalizeText(domain).toLowerCase()
  return normalized.replace(/^www\./, '')
}

const resolveCompany = (domain: string | null) => {
  const normalized = normalizeDomain(domain)
  if (!normalized) {
    return UNKNOWN_COMPANY
  }

  const companyToken = normalized.split('.').find(Boolean)
  if (!companyToken) {
    return UNKNOWN_COMPANY
  }

  return toTitleCase(companyToken)
}

const resolveSource = (domain: string | null) => {
  const normalized = normalizeDomain(domain)
  return normalized || UNKNOWN_SOURCE
}

const resolvePostedDate = (createdAt: string | null) => {
  const normalized = normalizeText(createdAt)
  if (!normalized) {
    return UNKNOWN_POSTED_DATE
  }

  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return UNKNOWN_POSTED_DATE
  }

  return parsed.toISOString().slice(0, 10)
}

const resolveSourceUrl = (finalUrl: string | null, rawUrl: string | null) => {
  const candidate = normalizeText(finalUrl) || normalizeText(rawUrl)
  if (!candidate) {
    return null
  }

  try {
    const parsed = new URL(candidate)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null
    }
    return parsed.toString()
  } catch {
    return null
  }
}

const toDisplayResult = (result: ResultRecord): ResultDisplayRecord => ({
  ...result,
  title: normalizeText(result.title) || '(Untitled result)',
  company: resolveCompany(result.domain),
  snippet: normalizeText(result.snippet) || 'No snippet available.',
  source: resolveSource(result.domain),
  postedDate: resolvePostedDate(result.createdAt),
  sourceUrl: resolveSourceUrl(result.finalUrl, result.rawUrl),
})

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
  const records = await handleResponse<ResultRecord[]>(response)
  return records.map(toDisplayResult)
}
