import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";

export function Layout() {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      navigate("/login");
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-card)] sticky top-0 z-50">
        <div className="container">
          <div className="flex h-16 items-center justify-between">
            <NavLink to="/skills" className="flex items-center gap-2 font-semibold text-lg text-[var(--color-text)]">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--color-primary)]">
                <path d="M18 6a6 6 0 0 1 0 12H6a6 6 0 0 1 0-12h12z" />
                <path d="M12 6v12" />
                <path d="M6 12h12" />
              </svg>
              <span>Beacon Console</span>
            </NavLink>

            <nav className="hidden md:flex items-center gap-1">
              <NavLink
                to="/skills"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                      : "text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]"
                  }`}
              >
                Skills
              </NavLink>
              <NavLink
                to="/executions"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                      : "text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]"
                  }`}
              >
                Executions
              </NavLink>
              <NavLink
                to="/settings"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                      : "text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]"
                  }`}
              >
                Settings
              </NavLink>
            </nav>

            <div className="flex items-center gap-3">
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-bg)] transition-colors"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="true"
                >
                  <div className="w-8 h-8 rounded-full bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)] font-medium">
                    U
                  </div>
                  <span className="hidden sm:block">User</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="hidden sm:block">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>

                {userMenuOpen && (
                  <div className="dropdown-menu">
                    <div className="px-3 py-2 border-b border-[var(--color-border)] text-sm text-[var(--color-text-muted)]">
                      Signed in as User
                    </div>
                    <button
                      onClick={handleLogout}
                      className="dropdown-item w-full text-left text-[var(--color-danger)]"
                    >
                      Log out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 container py-6">
        <Outlet />
      </main>

      <footer className="border-t border-[var(--color-border)] bg-[var(--color-bg-card)] py-4">
        <div className="container text-center text-sm text-[var(--color-text-muted)]">
          Beacon Console &mdash; AI Scientist Skills Platform &mdash; Ryan Vo <span>ryandtvo@gmail.com</span>
        </div>
      </footer>
    </div>
  );
}