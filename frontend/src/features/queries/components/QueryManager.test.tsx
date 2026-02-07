import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryManager } from './QueryManager'

const mockUseQueries = vi.fn()
const mockCreateMutate = vi.fn()
const mockUpdateMutate = vi.fn()

vi.mock('../hooks/use-queries', () => ({
  useQueries: () => mockUseQueries(),
  useCreateQuery: () => ({ mutate: mockCreateMutate, isPending: false }),
  useUpdateQuery: () => ({ mutate: mockUpdateMutate, isPending: false }),
}))

const sampleQueries = [
  {
    id: 'query-1',
    text: 'Senior Designer',
    enabled: true,
    createdAt: '2026-02-07T10:00:00Z',
    updatedAt: '2026-02-07T10:00:00Z',
  },
]

describe('QueryManager', () => {
  beforeEach(() => {
    mockCreateMutate.mockReset()
    mockUpdateMutate.mockReset()
    mockUseQueries.mockReturnValue({
      data: sampleQueries,
      isLoading: false,
      isError: false,
      error: null,
    })
  })

  it('submits new query text', async () => {
    const user = userEvent.setup()
    render(<QueryManager />)

    await user.type(screen.getByPlaceholderText(/e.g./i), 'Data analyst')
    await user.click(screen.getByRole('button', { name: /add query/i }))

    expect(mockCreateMutate).toHaveBeenCalledWith('Data analyst', expect.any(Object))
  })

  it('sends enable toggle updates', async () => {
    const user = userEvent.setup()
    render(<QueryManager />)

    await user.click(screen.getByRole('button', { name: /disable/i }))

    expect(mockUpdateMutate).toHaveBeenCalledWith(
      { id: 'query-1', update: { enabled: false } },
      expect.any(Object),
    )
  })

  it('edits query text', async () => {
    const user = userEvent.setup()
    render(<QueryManager />)

    await user.click(screen.getByRole('button', { name: /edit/i }))
    const input = screen.getByDisplayValue('Senior Designer')
    await user.clear(input)
    await user.type(input, 'Staff Designer')
    await user.click(screen.getByRole('button', { name: /save/i }))

    expect(mockUpdateMutate).toHaveBeenCalledWith(
      { id: 'query-1', update: { text: 'Staff Designer' } },
      expect.any(Object),
    )
  })
})
