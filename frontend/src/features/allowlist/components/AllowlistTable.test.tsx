import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { AllowlistTable } from './AllowlistTable'

const entries = [
  { domain: 'example.com', enabled: true },
  { domain: 'jobs.example.com', enabled: false },
]

describe('AllowlistTable', () => {
  it('renders entries and triggers actions', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    const onEdit = vi.fn()

    render(
      <AllowlistTable
        entries={entries}
        onToggle={onToggle}
        onEdit={onEdit}
      />,
    )

    expect(screen.getByText('example.com')).toBeInTheDocument()
    expect(screen.getByText('jobs.example.com')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /disable example\.com/i }))
    expect(onToggle).toHaveBeenCalledWith(entries[0], false)

    await user.click(screen.getByRole('button', { name: /edit jobs\.example\.com/i }))
    expect(onEdit).toHaveBeenCalledWith(entries[1])
  })
})
