import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from './AppLayout'
import { AllowlistPage } from '../features/allowlist'
import { QueryPage } from '../features/queries'
import { RunPage } from '../features/runs'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <AllowlistPage />,
      },
      {
        path: 'queries',
        element: <QueryPage />,
      },
      {
        path: 'runs',
        element: <RunPage />,
      },
    ],
  },
])
