import { useEffect, useState } from "react"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import { LevelPill } from "../components/LevelPill.tsx"
import type { Sistema } from "../types.ts"

export function HomePage() {
  const { user } = useAuth()
  const [sistema, setSistema] = useState<Sistema | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancel = false
    api<Sistema>("/api/sistema/")
      .then((next) => {
        if (!cancel) setSistema(next)
      })
      .catch((cause) => {
        if (!cancel) {
          setError(cause instanceof ApiError ? cause.message : "No se pudo cargar la operación.")
        }
      })
    return () => {
      cancel = true
    }
  }, [])

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Hoy</p>
          <h1>Hola, {user?.first_name || user?.username}.</h1>
          <p className="lede">{user?.role?.summary}</p>
        </div>
        <div className="role-card">
          <p className="eyebrow">Tu rol</p>
          <p className="role-card-name">{user?.role?.name}</p>
        </div>
      </header>

      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}

      <section className="policy">
        <p>{sistema?.politica_devolucion ?? "No se devuelve producto, salvo que esté en mal estado."}</p>
        <p className="policy-meta">
          La bodega principal reparte a {sistema?.puntos_de_venta ?? 5} puntos de venta.
        </p>
      </section>

      <section>
        <h2>Recorrido del día</h2>
        <p className="section-note">Tu rol queda marcado en cada paso. Consulta no es lo mismo que operar.</p>
        <ol className="flow">
          {(sistema?.flujo ?? []).map((step) => (
            <li key={step.code} className={step.participa ? "flow-step participates" : "flow-step"}>
              <span className="flow-order">{step.order}</span>
              <div>
                <div className="flow-title">
                  <h3>{step.title}</h3>
                  <LevelPill level={step.nivel} label={step.nivel_label} />
                </div>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="roadmap">
        <p className="eyebrow">Módulo en curso</p>
        <h2>Usuarios y roles</h2>
        <p>
          El siguiente módulo es el ingreso de producto a bodega: cargarlo al sistema, armar los camiones
          y despacharlos a los puntos.
        </p>
      </section>
    </div>
  )
}
