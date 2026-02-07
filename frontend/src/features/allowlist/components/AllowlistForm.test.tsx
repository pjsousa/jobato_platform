import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { AllowlistForm } from './AllowlistForm'

describe('AllowlistForm', () => {
  it('submits the entered domain', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <AllowlistForm
        mode="create"
        onSubmit={onSubmit}
        isSubmitting={false}
      />,
    )

    await user.type(screen.getByLabelText(/domain/i), 'example.com')
    await user.click(screen.getByRole('button', { name: /add domain/i }))

    expect(onSubmit).toHaveBeenCalledWith('example.com')
  })
})
