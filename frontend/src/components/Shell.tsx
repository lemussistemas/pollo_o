import { NavLink, Outlet } from "react-router-dom"

import { useAuth } from "../auth/useAuth.ts"

export function Shell() {
  const { user, logout, can } = useAuth()
  const seesUsers = can("usuarios.ver") || can("usuarios.gestionar")

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            P
          </span>
          <div>
            <p className="brand-kicker">Distribuidora</p>
            <p className="brand-name">Pollo</p>
          </div>
        </div>
        <nav className="nav" aria-label="Módulos">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
            El día
          </NavLink>
          <NavLink to="/roles" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
            Roles
          </NavLink>
          {seesUsers ? (
            <NavLink
              to="/usuarios"
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              Usuarios
            </NavLink>
          ) : null}
        </nav>
        <div className="sidebar-user">
          <p className="user-name">{user?.full_name}</p>
          <p className="user-role">{user?.role?.name ?? "Sin rol"}</p>
          <button type="button" className="button button-quiet" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
