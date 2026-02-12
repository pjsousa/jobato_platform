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

    expect(screen.getAllByText(/running/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/run-123/i)).toBeInTheDocument()
  })

  it('renders report summary metrics when available', () => {
    render(
      <RunStatus
        run={{
          runId: 'run-321',
          status: 'completed',
          startedAt: '2026-02-07T12:00:00Z',
          endedAt: '2026-02-07T12:02:05Z',
          statusReason: null,
        }}
        summary={{
          runId: 'run-321',
          status: 'completed',
          triggerTime: '2026-02-07T12:00:00Z',
          durationMs: 125000,
          newJobsCount: 12,
          relevantCount: 3,
        }}
      />,
    )

    expect(screen.getByText(/^12$/)).toBeInTheDocument()
    expect(screen.getByText(/^3$/)).toBeInTheDocument()
    expect(screen.getByText('2m 5s')).toBeInTheDocument()
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

    expect(screen.getByText(/quota reached/i)).toBeInTheDocument()
    expect(screen.getByText(/results are partial/i)).toBeInTheDocument()
  })
})
