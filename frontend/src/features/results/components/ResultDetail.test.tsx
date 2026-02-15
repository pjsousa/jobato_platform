import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ResultDetail } from './ResultDetail'

const createResult = (overrides: Partial<Record<string, unknown>> = {}) => ({
  id: 1,
  runId: 'run-1',
  queryId: 'query-1',
  queryText: 'query text',
  searchQuery: 'search terms',
  domain: 'example.com',
  title: 'Result title',
  company: 'Example',
  snippet: 'Example snippet',
  source: 'example.com',
  postedDate: '2026-02-14',
  sourceUrl: 'https://example.com/post',
  rawUrl: 'https://example.com/raw',
  finalUrl: 'https://example.com/post',
  createdAt: '2026-02-14T10:00:00Z',
  rawHtmlPath: null,
  visibleText: null,
  cacheKey: 'cache-key',
  cachedAt: null,
  lastSeenAt: null,
  normalizedUrl: 'https://example.com/post',
  canonicalId: null,
  isDuplicate: false,
  isHidden: false,
  duplicateCount: 0,
  relevanceScore: 0.5,
  scoredAt: '2026-02-14T10:00:00Z',
  scoreVersion: 'baseline',
  manualLabel: null as 'relevant' | 'irrelevant' | null,
  manualLabelUpdatedAt: null as string | null,
  ...overrides,
})

describe('ResultDetail', () => {
  it('hides manual label pill when label is null', () => {
    render(
      <ResultDetail
        selectedResult={createResult({ manualLabel: null })}
        isLoading={false}
        isEmpty={false}
        onCycleManualLabel={vi.fn()}
        isFeedbackPending={false}
        feedbackErrorMessage={null}
      />,
    )

    expect(screen.queryByText('Relevant')).toBeNull()
    expect(screen.queryByText('Irrelevant')).toBeNull()
  })

  it('renders manual label pill for non-null labels', () => {
    const { rerender } = render(
      <ResultDetail
        selectedResult={createResult({ manualLabel: 'relevant' })}
        isLoading={false}
        isEmpty={false}
        onCycleManualLabel={vi.fn()}
        isFeedbackPending={false}
        feedbackErrorMessage={null}
      />,
    )

    expect(screen.getByText('Relevant')).toBeTruthy()

    rerender(
      <ResultDetail
        selectedResult={createResult({ manualLabel: 'irrelevant' })}
        isLoading={false}
        isEmpty={false}
        onCycleManualLabel={vi.fn()}
        isFeedbackPending={false}
        feedbackErrorMessage={null}
      />,
    )

    expect(screen.getByText('Irrelevant')).toBeTruthy()
  })

  it('applies de-emphasis class when selected result is irrelevant', () => {
    const { container } = render(
      <ResultDetail
        selectedResult={createResult({ manualLabel: 'irrelevant' })}
        isLoading={false}
        isEmpty={false}
        onCycleManualLabel={vi.fn()}
        isFeedbackPending={false}
        feedbackErrorMessage={null}
      />,
    )

    const detailsRoot = container.querySelector('.result-details')
    expect(detailsRoot?.className).toContain('result-details--irrelevant')
    expect(screen.getByText('Irrelevant')).toBeTruthy()
  })

  it('disables title activation while feedback mutation is pending', async () => {
    const onCycleManualLabel = vi.fn()
    const user = userEvent.setup()

    render(
      <ResultDetail
        selectedResult={createResult({ manualLabel: null })}
        isLoading={false}
        isEmpty={false}
        onCycleManualLabel={onCycleManualLabel}
        isFeedbackPending={true}
        feedbackErrorMessage={null}
      />,
    )

    const button = screen.getByRole('button', { name: /cycle manual feedback label/i })
    expect(button.getAttribute('disabled')).not.toBeNull()

    await user.click(button)
    expect(onCycleManualLabel).not.toHaveBeenCalled()
  })
})
