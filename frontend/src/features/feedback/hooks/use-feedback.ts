import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ManualLabel, ResultDisplayRecord } from '../../results/api/results-api'
import { ApiError } from '../../results/api/results-api'
import { setFeedback, type SetFeedbackInput } from '../api/feedback-api'

type OptimisticContext = {
  snapshots: Array<[readonly unknown[], ResultDisplayRecord[] | undefined]>
}

export const useFeedback = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: setFeedback,
    onMutate: async (variables: SetFeedbackInput): Promise<OptimisticContext> => {
      await queryClient.cancelQueries({ queryKey: ['results'] })

      const snapshots = queryClient.getQueriesData<ResultDisplayRecord[]>({ queryKey: ['results'] })
      const optimisticUpdatedAt = new Date().toISOString()

      snapshots.forEach(([queryKey, data]) => {
        if (!data) {
          return
        }

        const nextData = data.map((item) =>
          item.id === variables.resultId
            ? {
                ...item,
                manualLabel: variables.label,
                manualLabelUpdatedAt: optimisticUpdatedAt,
              }
            : item,
        )
        queryClient.setQueryData(queryKey, nextData)
      })

      return { snapshots }
    },
    onError: (_error, _variables, context) => {
      context?.snapshots.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data)
      })
    },
    onSuccess: (response) => {
      const nextLabel: ManualLabel = response.manualLabel

      const queries = queryClient.getQueriesData<ResultDisplayRecord[]>({ queryKey: ['results'] })
      queries.forEach(([queryKey, data]) => {
        if (!data) {
          return
        }

        const nextData = data.map((item) =>
          item.id === response.resultId
            ? {
                ...item,
                manualLabel: nextLabel,
                manualLabelUpdatedAt: response.manualLabelUpdatedAt,
              }
            : item,
        )
        queryClient.setQueryData(queryKey, nextData)
      })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['results'] })
    },
  })
}

export const getFeedbackErrorMessage = (error: unknown) => {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Unable to save feedback right now.'
}
