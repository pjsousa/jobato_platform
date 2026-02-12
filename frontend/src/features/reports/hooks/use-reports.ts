import { useQuery } from '@tanstack/react-query'

import { getLatestRunSummary } from '../api/reports-api'

export const useLatestRunSummary = () =>
  useQuery({
    queryKey: ['reports', 'runs', 'latest'],
    queryFn: getLatestRunSummary,
  })
