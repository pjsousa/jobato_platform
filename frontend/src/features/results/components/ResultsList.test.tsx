import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ResultsList } from './ResultsList'

const createResult = (id: number, title: string, manualLabel: 'relevant' | 'irrelevant' | null) => ({
  id,
  runId: 'run-1',
  queryId: 'query-1',
  queryText: 'query text',
  searchQuery: 'search terms',
  domain: 'example.com',
  title,
  company: 'Example',
  snippet: `${title} snippet`,
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
  normalizedUrl: null,
  canonicalId: null,
  isDuplicate: false,
  isHidden: false,
  duplicateCount: 0,
  relevanceScore: 0.5,
  scoredAt: '2026-02-14T10:00:00Z',
  scoreVersion: 'baseline',
  manualLabel,
  manualLabelUpdatedAt: null,
})

describe('ResultsList', () => {
  it('applies de-emphasis class and keeps irrelevant label visible', () => {
    render(
      <ResultsList
        results={[createResult(1, 'Relevant item', 'relevant'), createResult(2, 'Irrelevant item', 'irrelevant')]}
        selectedResultId={2}
        onSelectResult={vi.fn()}
        isLoading={false}
        isEmpty={false}
        errorMessage={null}
        emptyStateMessage="No items"
        hiddenIrrelevantCount={0}
        showIrrelevant={true}
      />,
    )

    const irrelevantRow = screen.getByRole('button', { name: /irrelevant item/i })
    expect(irrelevantRow.className).toContain('results-item--irrelevant')
    expect(screen.getByText('Irrelevant')).toBeTruthy()
  })

  it('shows visible-count heading and hidden helper when toggle is off', () => {
    render(
      <ResultsList
        results={[createResult(1, 'Visible item', null)]}
        selectedResultId={1}
        onSelectResult={vi.fn()}
        isLoading={false}
        isEmpty={false}
        errorMessage={null}
        emptyStateMessage="No items"
        hiddenIrrelevantCount={2}
        showIrrelevant={false}
      />,
    )

    expect(screen.getByRole('heading', { level: 2, name: 'Result list (1)' })).toBeTruthy()
    expect(screen.getByText('2 irrelevant result(s) hidden.')).toBeTruthy()
  })
})
