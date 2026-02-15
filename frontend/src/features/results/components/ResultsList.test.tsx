import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
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

    const irrelevantRow = screen.getByRole('option', { name: /irrelevant item/i })
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

  it('supports ArrowUp, ArrowDown, Home, and End on listbox focus', async () => {
    const user = userEvent.setup()

    const KeyboardHarness = () => {
      const [selectedId, setSelectedId] = useState<number | null>(2)

      return (
        <ResultsList
          results={[createResult(1, 'First item', null), createResult(2, 'Second item', null), createResult(3, 'Third item', null)]}
          selectedResultId={selectedId}
          onSelectResult={setSelectedId}
          isLoading={false}
          isEmpty={false}
          errorMessage={null}
          emptyStateMessage="No items"
          hiddenIrrelevantCount={0}
          showIrrelevant={true}
        />
      )
    }

    render(<KeyboardHarness />)

    const listbox = screen.getByRole('listbox', { name: /search results/i })
    await user.click(listbox)
    expect(listbox).toHaveFocus()
    expect(listbox).toHaveAttribute('aria-activedescendant', 'results-option-2')

    await user.keyboard('{ArrowDown}')
    expect(listbox).toHaveAttribute('aria-activedescendant', 'results-option-3')

    await user.keyboard('{ArrowUp}')
    expect(listbox).toHaveAttribute('aria-activedescendant', 'results-option-2')

    await user.keyboard('{Home}')
    expect(listbox).toHaveAttribute('aria-activedescendant', 'results-option-1')

    await user.keyboard('{End}')
    expect(listbox).toHaveAttribute('aria-activedescendant', 'results-option-3')
  })

  it('keeps listbox focus after row click for deterministic keyboard flow', async () => {
    const user = userEvent.setup()

    render(
      <ResultsList
        results={[createResult(1, 'Focusable row', null), createResult(2, 'Other row', null)]}
        selectedResultId={1}
        onSelectResult={vi.fn()}
        isLoading={false}
        isEmpty={false}
        errorMessage={null}
        emptyStateMessage="No items"
        hiddenIrrelevantCount={0}
        showIrrelevant={true}
      />,
    )

    const listbox = screen.getByRole('listbox', { name: /search results/i })
    await user.click(screen.getByRole('button', { name: /focusable row/i }))

    expect(listbox).toHaveFocus()
  })
})
