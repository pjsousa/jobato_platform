export type RunSummaryResponse = {
  runId: string
  status: string
  triggerTime: string
  durationMs: number
  newJobsCount: number
  relevantCount: number
}

type ApiProblem = {
  title?: string
  detail?: string
}

export class ReportsApiError extends Error {
  problem?: ApiProblem

  constructor(message: string, problem?: ApiProblem) {
    super(message)
    this.problem = problem
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:18080/api').replace(/\/$/, '')
const latestRunSummaryUrl = `${API_BASE_URL}/reports/runs/latest`

const parseProblem = async (response: Response): Promise<ApiProblem | undefined> => {
  try {
    return (await response.json()) as ApiProblem
  } catch {
    return undefined
  }
}

export const getLatestRunSummary = async (): Promise<RunSummaryResponse | null> => {
  const response = await fetch(latestRunSummaryUrl)
  if (response.status === 204) {
    return null
  }
  if (!response.ok) {
    const problem = await parseProblem(response)
    throw new ReportsApiError(problem?.detail ?? problem?.title ?? 'Failed to load run summary', problem)
  }
  return (await response.json()) as RunSummaryResponse
}
