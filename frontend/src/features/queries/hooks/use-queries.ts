import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createQuery, getQueries, updateQuery, type QueryUpdate } from '../api/queries'

export const useQueries = () =>
  useQuery({
    queryKey: ['queries'],
    queryFn: getQueries,
  })

export const useCreateQuery = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createQuery,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['queries'] }),
  })
}

type UpdatePayload = {
  id: string
  update: QueryUpdate
}

export const useUpdateQuery = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, update }: UpdatePayload) => updateQuery(id, update),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['queries'] }),
  })
}
