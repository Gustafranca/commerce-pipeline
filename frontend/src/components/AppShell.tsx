import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  ].join(" ");

export function AppShell() {
  const { isLoggedIn, username, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex flex-wrap items-baseline gap-3">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-semibold text-slate-900">Pipeline Commerce</span>
              <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Dashboard</span>
            </div>
            {isLoggedIn ? (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <span className="font-medium text-slate-800">{username}</span>
                <button
                  type="button"
                  className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  onClick={() => logout()}
                >
                  Sign out
                </button>
              </div>
            ) : null}
          </div>
          <nav className="flex flex-wrap gap-1">
            <NavLink to="/" className={linkClass} end>
              Ingest
            </NavLink>
            <NavLink to="/staged" className={linkClass}>
              Staged
            </NavLink>
            <NavLink to="/browse" className={linkClass}>
              Browse
            </NavLink>
            <NavLink to="/explorer" className={linkClass}>
              Explorer
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
