import { NavLink, Outlet } from "react-router-dom";

function linkClass(isActive: boolean) {
  return `nav-link${isActive ? " active" : ""}`;
}

export function LayoutShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>FairLens</h1>
        <nav>
          <NavLink to="/" className={({ isActive }) => linkClass(isActive)} end>
            Dashboard
          </NavLink>
          <NavLink to="/audits/new" className={({ isActive }) => linkClass(isActive)}>
            New Audit
          </NavLink>
          <NavLink to="/metrics" className={({ isActive }) => linkClass(isActive)}>
            Metrics
          </NavLink>
        </nav>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
