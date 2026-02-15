import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ResultsPage } from './ResultsPage'

const mockUseResults = vi.fn()
const mockUseFeedback = vi.fn()

vi.mock('../hooks/use-results', () => ({
  useResults: (view: 'today' | 'all-time') => mockUseResults(view),
}))

vi.mock('../../feedback', () => ({
  useFeedback: () => mockUseFeedback(),
  getFeedbackErrorMessage: (error: unknown) => (error instanceof Error ? error.message : 'Unable to save feedback right now.'),
}))

const createResult = (
  id: number,
  title: string,
  runId: string,
  overrides: Partial<Record<string, unknown>> = {},
) => ({
  id,
  runId,
  queryId: 'query-1',
  queryText: 'query text',
  searchQuery: 'search terms',
  domain: 'example.com',
  title,
  company: 'Example',
  snippet: `${title} snippet`,
  source: 'example.com',
  postedDate: '2026-02-14',
  sourceUrl: 'https://example.com/final',
  rawUrl: 'https://example.com/raw',
  finalUrl: 'https://example.com/final',
  createdAt: '2026-02-14T10:00:00Z',
  rawHtmlPath: null,
  visibleText: null,
  cacheKey: 'cache-key',
  cachedAt: null,
  lastSeenAt: null,
  normalizedUrl: null,
  canonicalId: null,
  isDuplicate: false,
  isHidden: false,
  duplicateCount: 0,
  relevanceScore: 0.8,
  scoredAt: '2026-02-14T10:00:00Z',
  scoreVersion: 'baseline',
  manualLabel: null as 'relevant' | 'irrelevant' | null,
  manualLabelUpdatedAt: null as string | null,
  ...overrides,
})

const renderPage = (initialEntry = '/results') => {
  const router = createMemoryRouter([{ path: '/results', element: <ResultsPage /> }], {
    initialEntries: [initialEntry],
  })

  const renderResult = render(<RouterProvider router={router} />)
  return { router, ...renderResult }
}

describe('ResultsPage', () => {
  beforeEach(() => {
    mockUseResults.mockReset()
    mockUseFeedback.mockReset()
    mockUseFeedback.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    })
  })

  it('defaults to today and updates URL on tab switch', async () => {
    const todayResults = [createResult(1, 'Today first', 'run-today')]
    const allTimeResults = [createResult(2, 'All-time first', 'run-old')]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? todayResults : allTimeResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    const { router } = renderPage('/results')

    await waitFor(() => {
      expect(router.state.location.search).toBe('?view=today')
    })

    await user.click(screen.getByRole('tab', { name: /all time/i }))

    await waitFor(() => {
      expect(router.state.location.search).toBe('?view=all-time')
    })
    expect(mockUseResults).toHaveBeenCalledWith('all-time')
  })

  it('defaults to the first today result and hydrates detail', () => {
    const todayResults = [createResult(1, 'Today first', 'run-today'), createResult(2, 'Today second', 'run-today')]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? todayResults : [],
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    renderPage('/results?view=today')

    expect(screen.getByRole('heading', { level: 3, name: 'Today first' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /today first/i })).toHaveClass('selected')
  })

  it('updates highlight and detail when selecting another row', async () => {
    const todayResults = [createResult(1, 'Today first', 'run-today'), createResult(2, 'Today second', 'run-today')]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? todayResults : [],
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /today second/i }))

    expect(screen.getByRole('heading', { level: 3, name: 'Today second' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /today second/i })).toHaveClass('selected')
  })

  it('preserves selected result when it exists in the next query result set', async () => {
    const todayResults = [createResult(1, 'Today first', 'run-today'), createResult(2, 'Shared result', 'run-today')]
    const allTimeResults = [createResult(2, 'Shared result', 'run-older'), createResult(3, 'All-time only', 'run-older')]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? todayResults : allTimeResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /shared result/i }))
    await user.click(screen.getByRole('tab', { name: /all time/i }))

    expect(screen.getByRole('heading', { level: 3, name: 'Shared result' })).toBeInTheDocument()
  })

  it('falls back to first result when previous selection disappears in next query result set', async () => {
    const todayResults = [createResult(1, 'Today first', 'run-today'), createResult(2, 'Today second', 'run-today')]
    const allTimeResults = [createResult(4, 'All-time first', 'run-older')]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? todayResults : allTimeResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /today second/i }))
    await user.click(screen.getByRole('tab', { name: /all time/i }))

    expect(screen.getByRole('heading', { level: 3, name: 'All-time first' })).toBeInTheDocument()
  })

  it('hides irrelevant rows by default and shows visible result count', () => {
    const todayResults = [
      createResult(1, 'Relevant first', 'run-today', { manualLabel: 'relevant' }),
      createResult(2, 'Irrelevant second', 'run-today', { manualLabel: 'irrelevant' }),
      createResult(3, 'Unlabeled third', 'run-today', { manualLabel: null }),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const { router } = renderPage('/results?view=today')

    expect(router.state.location.search).toBe('?view=today')
    expect(screen.getByRole('heading', { level: 2, name: 'Result list (2)' })).toBeInTheDocument()
    expect(screen.getByText('1 irrelevant result(s) hidden.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /irrelevant second/i })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 3, name: 'Relevant first' })).toBeInTheDocument()
  })

  it('shows irrelevant rows when toggled and keeps URL history state', async () => {
    const todayResults = [
      createResult(1, 'Relevant first', 'run-today', { manualLabel: 'relevant' }),
      createResult(2, 'Irrelevant second', 'run-today', { manualLabel: 'irrelevant' }),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    const { router } = renderPage('/results?view=today&runId=run-42')

    await user.click(screen.getByLabelText(/show irrelevant/i))

    await waitFor(() => {
      expect(router.state.location.search).toBe('?view=today&runId=run-42&showIrrelevant=true')
    })
    expect(screen.getByRole('heading', { level: 2, name: 'Result list (2)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /irrelevant second/i })).toBeInTheDocument()

    await act(async () => {
      await router.navigate(-1)
    })
    await waitFor(() => {
      expect(router.state.location.search).toBe('?view=today&runId=run-42')
    })
    expect(screen.queryByRole('button', { name: /irrelevant second/i })).not.toBeInTheDocument()

    await act(async () => {
      await router.navigate(1)
    })
    await waitFor(() => {
      expect(router.state.location.search).toBe('?view=today&runId=run-42&showIrrelevant=true')
    })
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /irrelevant second/i })).toBeInTheDocument()
    })
  })

  it('falls back to the next visible result when selected irrelevant is hidden', async () => {
    const todayResults = [
      createResult(1, 'Relevant first', 'run-today', { manualLabel: 'relevant' }),
      createResult(2, 'Irrelevant second', 'run-today', { manualLabel: 'irrelevant' }),
      createResult(3, 'Relevant third', 'run-today', { manualLabel: null }),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today&showIrrelevant=true')

    await user.click(screen.getByRole('button', { name: /irrelevant second/i }))
    expect(screen.getByRole('heading', { level: 3, name: 'Irrelevant second' })).toBeInTheDocument()

    await user.click(screen.getByLabelText(/show irrelevant/i))

    expect(screen.queryByRole('button', { name: /irrelevant second/i })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 3, name: 'Relevant third' })).toBeInTheDocument()
  })

  it('keeps selection when crossing breakpoint widths', async () => {
    const todayResults = [createResult(1, 'Today first', 'run-today'), createResult(2, 'Today second', 'run-today')]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /today second/i }))

    window.innerWidth = 900
    window.dispatchEvent(new Event('resize'))
    window.innerWidth = 1280
    window.dispatchEvent(new Event('resize'))

    expect(screen.getByRole('heading', { level: 3, name: 'Today second' })).toBeInTheDocument()
  })

  it('keeps API ordering in the rendered list', () => {
    const orderedResults = [
      createResult(3, 'First from API', 'run-today'),
      createResult(1, 'Second from API', 'run-today'),
      createResult(2, 'Third from API', 'run-today'),
    ]

    mockUseResults.mockImplementation((view: 'today' | 'all-time') => ({
      data: view === 'today' ? orderedResults : [],
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    renderPage('/results?view=today')

    const renderedTitles = Array.from(document.querySelectorAll('.results-item__title')).map(
      (node) => node.textContent,
    )
    expect(renderedTitles).toEqual(['First from API', 'Second from API', 'Third from API'])
  })

  it('keeps selected id stable across refetch when still visible', async () => {
    let todayResults = [
      createResult(1, 'First from API', 'run-today'),
      createResult(2, 'Selected stays', 'run-today'),
      createResult(3, 'Third from API', 'run-today'),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    const { rerender, router } = renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /selected stays/i }))
    expect(screen.getByRole('heading', { level: 3, name: 'Selected stays' })).toBeInTheDocument()

    todayResults = [
      createResult(3, 'Third from API', 'run-today'),
      createResult(2, 'Selected stays', 'run-today'),
      createResult(1, 'First from API', 'run-today'),
    ]

    rerender(<RouterProvider router={router} />)

    expect(screen.getByRole('heading', { level: 3, name: 'Selected stays' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /selected stays/i })).toHaveClass('selected')
  })

  it('renders required list metadata and only shows duplicate badge for positive counts', () => {
    const todayResults = [
      createResult(1, 'Canonical result', 'run-today', {
        company: 'Acme',
        snippet: 'Canonical snippet',
        source: 'acme.com',
        postedDate: '2026-01-10',
        duplicateCount: 2,
      }),
      createResult(2, 'Single result', 'run-today', {
        company: 'Solo',
        snippet: 'Single snippet',
        source: 'solo.io',
        postedDate: '2026-01-09',
        duplicateCount: 0,
      }),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    renderPage('/results?view=today')

    expect(screen.getAllByText('Acme').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Canonical snippet').length).toBeGreaterThan(0)
    expect(screen.getAllByText('acme.com').length).toBeGreaterThan(0)
    expect(screen.getAllByText('2026-01-10').length).toBeGreaterThan(0)
    expect(screen.getByText('2 duplicate(s)')).toBeInTheDocument()
    expect(screen.queryByText('0 duplicate(s)')).not.toBeInTheDocument()
  })

  it('shows canonical context and safe source links in detail pane', async () => {
    const todayResults = [
      createResult(1, 'Canonical result', 'run-today', {
        duplicateCount: 3,
        isDuplicate: false,
        canonicalId: null,
        sourceUrl: 'https://canonical.example.com/post',
      }),
      createResult(2, 'Duplicate result', 'run-today', {
        duplicateCount: 0,
        isDuplicate: true,
        canonicalId: 1,
        sourceUrl: 'https://duplicate.example.com/post',
      }),
    ]

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    expect(screen.getByText('This is the canonical result for 3 duplicate(s).')).toBeInTheDocument()
    const canonicalLink = screen.getByRole('link', { name: /open source page/i })
    expect(canonicalLink).toHaveAttribute('href', 'https://canonical.example.com/post')
    expect(canonicalLink).toHaveAttribute('target', '_blank')
    expect(canonicalLink).toHaveAttribute('rel', 'noopener noreferrer')

    await user.click(screen.getByRole('button', { name: /duplicate result/i }))
    expect(
      screen.getByText('This result is marked as a duplicate of canonical result #1.'),
    ).toBeInTheDocument()
  })

  it('shows loading, updating, and empty states and clears empty selection', () => {
    mockUseResults.mockImplementation((view: 'today' | 'all-time') => {
      if (view === 'today') {
        return {
          data: [],
          isLoading: false,
          isFetching: false,
          error: null,
        }
      }

      return {
        data: [createResult(8, 'Previous content', 'run-history')],
        isLoading: false,
        isFetching: true,
        error: null,
      }
    })

    const { unmount } = renderPage('/results?view=today')
    expect(screen.getByText(/no results in today's run yet/i)).toBeInTheDocument()
    expect(screen.getByText(/no result selected yet/i)).toBeInTheDocument()

    unmount()

    mockUseResults.mockImplementation(() => ({
      data: undefined,
      isLoading: true,
      isFetching: true,
      error: null,
    }))

    const { unmount: unmountLoading } = renderPage('/results?view=today')
    expect(screen.getByText(/loading results/i)).toBeInTheDocument()

    unmountLoading()

    mockUseResults.mockImplementation(() => ({
      data: [createResult(9, 'Previous content', 'run-history')],
      isLoading: false,
      isFetching: true,
      error: null,
    }))

    renderPage('/results?view=all-time')
    expect(screen.getByText(/updating results/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous content/i })).toBeInTheDocument()
  })

  it('cycles manual feedback via title activation and keeps list/detail pills in sync', async () => {
    let todayResults = [createResult(1, 'Cycle me', 'run-today', { manualLabel: null })]
    const mutate = vi.fn(({ resultId, label }: { resultId: number; label: 'relevant' | 'irrelevant' | null }) => {
      todayResults = todayResults.map((item) => (item.id === resultId ? { ...item, manualLabel: label } : item))
    })

    mockUseFeedback.mockReturnValue({
      mutate,
      isPending: false,
      isError: false,
      error: null,
    })

    mockUseResults.mockImplementation(() => ({
      data: todayResults,
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    const firstRender = renderPage('/results?view=today&showIrrelevant=true')

    await user.click(screen.getByRole('button', { name: /cycle manual feedback label/i }))
    expect(mutate).toHaveBeenNthCalledWith(1, { resultId: 1, label: 'relevant' })
    firstRender.unmount()

    const secondRender = renderPage('/results?view=today&showIrrelevant=true')
    expect(screen.getAllByText('Relevant').length).toBe(2)

    await user.click(screen.getByRole('button', { name: /cycle manual feedback label/i }))
    expect(mutate).toHaveBeenNthCalledWith(2, { resultId: 1, label: 'irrelevant' })
    secondRender.unmount()

    const thirdRender = renderPage('/results?view=today&showIrrelevant=true')
    expect(screen.getAllByText('Irrelevant').length).toBe(2)

    await user.click(screen.getByRole('button', { name: /cycle manual feedback label/i }))
    expect(mutate).toHaveBeenNthCalledWith(3, { resultId: 1, label: null })
    thirdRender.unmount()

    renderPage('/results?view=today&showIrrelevant=true')
    expect(screen.queryByText('Relevant')).not.toBeInTheDocument()
    expect(screen.queryByText('Irrelevant')).not.toBeInTheDocument()
  })

  it('blocks additional title cycles while feedback mutation is pending', async () => {
    const mutate = vi.fn()
    mockUseFeedback.mockReturnValue({
      mutate,
      isPending: true,
      isError: false,
      error: null,
    })
    mockUseResults.mockImplementation(() => ({
      data: [createResult(1, 'Pending cycle', 'run-today')],
      isLoading: false,
      isFetching: false,
      error: null,
    }))

    const user = userEvent.setup()
    renderPage('/results?view=today')

    await user.click(screen.getByRole('button', { name: /cycle manual feedback label/i }))

    expect(mutate).not.toHaveBeenCalled()
  })
})
