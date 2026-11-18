import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import { LevelPill } from "../components/LevelPill.tsx"
import type { Sistema } from "../types.ts"

export function HomePage() {
  const { user, can } = useAuth()
  const [sistema, setSistema] = useState<Sistema | null>(null)
  const [nuevos, setNuevos] = useState(0)
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

  useEffect(() => {
    if (!can("clientes.ver")) return
    let cancel = false
    api<{ nuevos: number }>("/api/clientes/avisos/")
      .then((data) => {
        if (!cancel) setNuevos(data.nuevos)
      })
      .catch(() => {})
    return () => {
      cancel = true
    }
  }, [can])

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

      {nuevos > 0 ? (
        <p className="ok">
          Hay {nuevos} {nuevos === 1 ? "cliente nuevo" : "clientes nuevos"} esta semana.{" "}
          <Link to="/clientes?nuevos=1">Verlos</Link>
        </p>
      ) : null}

      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}

      <section className="policy">
        <p>{sistema?.politica_devolucion}</p>
        <p className="policy-meta">
          La bodega seca abastece {(sistema?.puntos ?? []).map((punto) => punto.name).join(", ") || "los puntos de venta"}.
          En ruta salen {sistema?.vehiculos?.camiones ?? 3} camiones y {sistema?.vehiculos?.motocarga ?? 1} motocarga.
          Cada punto factura con su propio CAI.
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
        <h2>Carga</h2>
        <p>
          Inventario arma la carga de los tres camiones y la motocarga con lo que hay en bodega, lote por lote.
          Lo que sigue es el despacho a los cinco puntos.
        </p>
        {can("distribucion.carga") ? (
          <p>
            <Link to="/carga">Abrir la carga</Link>
          </p>
        ) : null}
      </section>
    </div>
  )
}
