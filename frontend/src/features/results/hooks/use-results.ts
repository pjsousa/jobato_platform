import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { getResults, type ResultRecord, type ResultsView } from '../api/results-api'

export const useResults = (view: ResultsView) =>
  useQuery<ResultRecord[]>({
    queryKey: ['results', { view }],
    queryFn: () => getResults({ view }),
    placeholderData: keepPreviousData,
  })
