import { useMutation, useQuery } from '@tanstack/react-query'

import { getRun, triggerRun } from '../api/runs-api'

export const useTriggerRun = () =>
  useMutation({
    mutationFn: triggerRun,
  })

export const useRun = (runId: string | null) =>
  useQuery({
    queryKey: ['runs', runId],
    queryFn: () => getRun(runId ?? ''),
    enabled: Boolean(runId),
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 5000 : false,
  })
