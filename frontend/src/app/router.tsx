import { createBrowserRouter } from 'react-router-dom'

import { AllowlistPage } from '../features/allowlist'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AllowlistPage />,
  },
])
