import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { getResults, type ResultDisplayRecord, type ResultsView } from '../api/results-api'

export const useResults = (view: ResultsView) =>
  useQuery<ResultDisplayRecord[]>({
    queryKey: ['results', { view }],
    queryFn: () => getResults({ view }),
    placeholderData: keepPreviousData,
  })
