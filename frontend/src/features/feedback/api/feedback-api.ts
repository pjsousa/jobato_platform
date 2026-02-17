import { ApiError, type ManualLabel } from '../../results/api/results-api'

type ApiProblem = {
  title?: string
  detail?: string
  errorCode?: string
  status?: number
}

type FeedbackResponse = {
  resultId: number
  manualLabel: ManualLabel
  manualLabelUpdatedAt: string | null
}

export type SetFeedbackInput = {
  resultId: number
  label: ManualLabel
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:18080/api').replace(/\/$/, '')
const baseUrl = `${API_BASE_URL}/feedback`

const parseProblem = async (response: Response): Promise<ApiProblem | undefined> => {
  try {
    return (await response.json()) as ApiProblem
  } catch {
    return undefined
  }
}

export const setFeedback = async ({ resultId, label }: SetFeedbackInput) => {
  const response = await fetch(baseUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ resultId, label }),
  })

  if (!response.ok) {
    const problem = await parseProblem(response)
    const message = problem?.detail || problem?.title || 'Unable to save feedback'
    throw new ApiError(message, problem)
  }

  return (await response.json()) as FeedbackResponse
}
