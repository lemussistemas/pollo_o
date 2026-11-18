import { Navigate, Route, Routes } from "react-router-dom"

import { useAuth } from "./auth/useAuth.ts"
import { Shell } from "./components/Shell.tsx"
import { HomePage } from "./pages/HomePage.tsx"
import { LoginPage } from "./pages/LoginPage.tsx"
import { RolesPage } from "./pages/RolesPage.tsx"
import { UsersPage } from "./pages/UsersPage.tsx"

function RequireAuth() {
  const { user, ready } = useAuth()
  if (!ready) return <p className="boot">Cargando sesión…</p>
  if (!user) return <Navigate to="/login" replace />
  return <Shell />
}

function GuestOnly() {
  const { user, ready } = useAuth()
  if (!ready) return <p className="boot">Cargando sesión…</p>
  if (user) return <Navigate to="/" replace />
  return <LoginPage />
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<GuestOnly />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/roles" element={<RolesPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
