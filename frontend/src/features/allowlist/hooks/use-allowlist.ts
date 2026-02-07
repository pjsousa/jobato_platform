import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createAllowlist, fetchAllowlists, updateAllowlist } from '../api/allowlist-api'
import type { AllowlistEntry, AllowlistUpdate } from '../api/allowlist-api'

const allowlistKey = ['allowlists']

export const useAllowlists = () =>
  useQuery<AllowlistEntry[]>({
    queryKey: allowlistKey,
    queryFn: fetchAllowlists,
  })

export const useCreateAllowlist = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (domain: string) => createAllowlist(domain),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: allowlistKey }),
  })
}

export const useUpdateAllowlist = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ currentDomain, update }: { currentDomain: string; update: AllowlistUpdate }) =>
      updateAllowlist(currentDomain, update),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: allowlistKey }),
  })
}
