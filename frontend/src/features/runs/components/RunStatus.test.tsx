import { render, screen } from '@testing-library/react'

import { RunStatus } from './RunStatus'

describe('RunStatus', () => {
  it('renders the running status', () => {
    render(
      <RunStatus
        run={{
          runId: 'run-123',
          status: 'running',
          startedAt: '2026-02-07T12:00:00Z',
          endedAt: null,
        }}
      />,
    )

    expect(screen.getByText(/running/i)).toBeInTheDocument()
    expect(screen.getByText(/run-123/i)).toBeInTheDocument()
  })

  it('shows an error banner when provided', () => {
    render(
      <RunStatus
        run={{
          runId: 'run-456',
          status: 'failed',
          startedAt: '2026-02-07T12:00:00Z',
          endedAt: '2026-02-07T12:10:00Z',
        }}
        errorMessage="Run already in progress"
      />,
    )

    expect(screen.getByText(/run already in progress/i)).toBeInTheDocument()
  })
})
