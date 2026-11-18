import { Navigate, Route, Routes } from "react-router-dom"

import { useAuth } from "./auth/useAuth.ts"
import { Shell } from "./components/Shell.tsx"
import { BooksPage } from "./pages/BooksPage.tsx"
import { WarehousePage } from "./pages/WarehousePage.tsx"
import { ClientsPage } from "./pages/ClientsPage.tsx"
import { LoadsPage } from "./pages/LoadsPage.tsx"
import { HomePage } from "./pages/HomePage.tsx"
import { LoginPage } from "./pages/LoginPage.tsx"
import { ProductsPage } from "./pages/ProductsPage.tsx"
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
        <Route path="/clientes" element={<ClientsPage />} />
        <Route path="/libros" element={<BooksPage />} />
        <Route path="/productos" element={<ProductsPage />} />
        <Route path="/bodega" element={<WarehousePage />} />
        <Route path="/carga" element={<LoadsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
