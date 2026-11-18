import { useState } from "react"
import type { FormEvent } from "react"

import { ApiError } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"

const STEPS = [
  "El pollo entra a la bodega principal y se carga al sistema.",
  "Se arman los camiones y se reparte a 5 puntos de venta.",
  "Facturación atiende los puntos. El vendedor factura en la tablet.",
  "Al regreso se vuelve a inventariar. Solo vuelve lo que está en mal estado.",
]

export function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setPending(true)
    try {
      await login(username, password)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo iniciar sesión.")
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="login">
      <section className="login-story">
        <p className="eyebrow">Bodega principal</p>
        <h1>El día del pollo, de la bodega al punto de venta.</h1>
        <ol className="story-list">
          {STEPS.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={onSubmit}>
          <p className="eyebrow">Entrar</p>
          <h2>Tu rol define qué puedes hacer hoy.</h2>
          <label>
            Usuario
            <input
              name="username"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            Contraseña
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error ? (
            <p className="notice" role="alert">
              {error}
            </p>
          ) : null}
          <button className="button" type="submit" disabled={pending}>
            {pending ? "Entrando…" : "Entrar"}
          </button>
          <details className="demo-access">
            <summary>Usuarios de prueba</summary>
            <p>Contraseña para los cinco: Pollo2026</p>
            <ul>
              <li>gerencia</li>
              <li>contador</li>
              <li>facturacion</li>
              <li>vendedor</li>
              <li>inventario</li>
            </ul>
          </details>
        </form>
      </section>
    </div>
  )
}
