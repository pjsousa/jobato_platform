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
          statusReason: null,
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
          statusReason: null,
        }}
        errorMessage="Run already in progress"
      />,
    )

    expect(screen.getByText(/run already in progress/i)).toBeInTheDocument()
  })

  it('shows quota reached messaging for partial runs', () => {
    render(
      <RunStatus
        run={{
          runId: 'run-789',
          status: 'partial',
          startedAt: '2026-02-07T12:00:00Z',
          endedAt: '2026-02-07T12:08:00Z',
          statusReason: 'quota-reached',
        }}
      />,
    )

    expect(screen.getAllByText(/quota reached/i).length).toBeGreaterThan(1)
    expect(screen.getByText(/results are partial/i)).toBeInTheDocument()
  })
})
