import { NavLink, Outlet } from 'react-router-dom'

import './AppLayout.css'

export const AppLayout = () => (
  <div className="app-shell">
    <header className="app-nav">
      <div className="app-brand">
        <span className="eyebrow">Search scope</span>
        <span className="app-brand__title">Run configuration</span>
      </div>
      <nav className="app-nav__links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `app-nav__link${isActive ? ' active' : ''}`}
        >
          Allowlist
        </NavLink>
        <NavLink
          to="/queries"
          className={({ isActive }) => `app-nav__link${isActive ? ' active' : ''}`}
        >
          Queries
        </NavLink>
        <NavLink
          to="/runs"
          className={({ isActive }) => `app-nav__link${isActive ? ' active' : ''}`}
        >
          Runs
        </NavLink>
        <NavLink
          to="/results"
          className={({ isActive }) => `app-nav__link${isActive ? ' active' : ''}`}
        >
          Results
        </NavLink>
      </nav>
    </header>
    <Outlet />
  </div>
)
