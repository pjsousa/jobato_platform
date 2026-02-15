import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ResultsPage } from './ResultsPage'

const mockUseResults = vi.fn()

vi.mock('../hooks/use-results', () => ({
  useResults: (view: 'today' | 'all-time') => mockUseResults(view),
}))

const createResult = (id: number, title: string, runId: string) => ({
  id,
  runId,
  queryId: 'query-1',
  queryText: 'query text',
  searchQuery: 'search terms',
  domain: 'example.com',
  title,
  snippet: `${title} snippet`,
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
})
