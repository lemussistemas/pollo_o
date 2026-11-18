import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { Carga, Existencia, Vehiculo } from "../types.ts"

function hoy() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${month}-${day}`
}

function fecha(value: string | null) {
  if (!value) return ""
  const [year, month, day] = value.slice(0, 10).split("-")
  return `${day}/${month}/${year}`
}

function cantidad(value: string, unidad: string) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return value
  const text = amount.toLocaleString("es-HN", { maximumFractionDigits: 3 })
  return `${text} ${unidad === "libra" ? "lb" : "und"}`
}

export function LoadsPage() {
  const { can } = useAuth()
  const canLoad = can("distribucion.carga", "operate")
  const [vehicles, setVehicles] = useState<Vehiculo[]>([])
  const [sellers, setSellers] = useState<{ id: number; full_name: string }[]>([])
  const [vehicleId, setVehicleId] = useState("")
  const [day, setDay] = useState(hoy)
  const [load, setLoad] = useState<Carga | null>(null)
  const [stock, setStock] = useState<Existencia[]>([])
  const [existenciaId, setExistenciaId] = useState("")
  const [amount, setAmount] = useState("")
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [revision, setRevision] = useState(0)

  const vehicle = vehicles.find((item) => String(item.id) === vehicleId)

  useEffect(() => {
    if (!can("distribucion.carga")) return
    let cancel = false
    api<{ vehiculos: Vehiculo[]; vendedores?: { id: number; full_name: string }[] }>("/api/distribucion/vehiculos/")
      .then((data) => {
        if (cancel) return
        setVehicles(data.vehiculos)
        setSellers(data.vendedores ?? [])
        setVehicleId((current) => current || (data.vehiculos[0] ? String(data.vehiculos[0].id) : ""))
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudieron leer los vehículos.")
      })
    return () => {
      cancel = true
    }
  }, [can])

  useEffect(() => {
    if (!can("distribucion.carga") || !vehicleId) return
    let cancel = false
    const params = new URLSearchParams({ vehiculo: vehicleId, fecha: day })
    api<Carga[]>(`/api/distribucion/cargas/?${params.toString()}`)
      .then((rows) => {
        if (!cancel) setLoad(rows[0] ?? null)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudo leer la carga.")
      })
    return () => {
      cancel = true
    }
  }, [can, vehicleId, day, revision])

  useEffect(() => {
    if (!canLoad) return
    let cancel = false
    api<Existencia[]>("/api/bodega/existencias/")
      .then((rows) => {
        if (!cancel) setStock(rows)
      })
      .catch(() => {
        if (!cancel) setStock([])
      })
    return () => {
      cancel = true
    }
  }, [canLoad, revision])

  if (!can("distribucion.carga")) return <Navigate to="/" replace />

  async function openLoad() {
    setError("")
    setNotice("")
    try {
      const opened = await api<Carga>("/api/distribucion/cargas/", {
        method: "POST",
        body: JSON.stringify({ vehiculo_id: Number(vehicleId), fecha: day }),
      })
      setLoad(opened)
      setNotice(`Carga de ${opened.vehiculo_nombre} lista.`)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo abrir la carga.")
    }
  }

  async function assignSeller(sellerId: string) {
    if (!vehicle) return
    setError("")
    try {
      const saved = await api<Vehiculo>(`/api/distribucion/vehiculos/${vehicle.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ vendedor_id: sellerId ? Number(sellerId) : null }),
      })
      setVehicles((current) => current.map((item) => (item.id === saved.id ? saved : item)))
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo asignar el vendedor.")
    }
  }

  async function addLine(event: FormEvent) {
    event.preventDefault()
    if (!load) return
    setError("")
    setNotice("")
    try {
      const saved = await api<Carga>(`/api/distribucion/cargas/${load.id}/lineas/`, {
        method: "POST",
        body: JSON.stringify({ existencia_id: Number(existenciaId), cantidad: amount }),
      })
      setLoad(saved)
      setAmount("")
      setNotice("La línea quedó en la carga y salió de bodega.")
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo cargar esa existencia.")
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Distribución</p>
          <h1>Carga de vehículos</h1>
          <p className="lede">
            Son tres camiones y una motocarga. Inventario arma la carga del día con la existencia de la bodega, sin
            pasar lo que hay de cada lote. El vendedor ve la carga del vehículo que tiene asignado.
          </p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="ok">{notice}</p> : null}
      <form className="filters">
        <label>
          Vehículo
          <select value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
            {vehicles.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fecha
          <input type="date" value={day} onChange={(event) => setDay(event.target.value)} />
        </label>
        {canLoad && vehicle ? (
          <label>
            Vendedor
            <select value={vehicle.vendedor ?? ""} onChange={(event) => assignSeller(event.target.value)}>
              <option value="">Sin asignar</option>
              {sellers.map((seller) => (
                <option key={seller.id} value={seller.id}>
                  {seller.full_name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </form>
      <div className={canLoad ? "users-layout" : "users-layout single"}>
        <section>
          <div className="table-wrap">
            <table>
              <caption>{load ? `${load.lineas.length} líneas` : "Sin carga"}</caption>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Lote</th>
                  <th>Vence</th>
                  <th className="money">Cantidad</th>
                </tr>
              </thead>
              <tbody>
                {(load?.lineas ?? []).map((line) => (
                  <tr key={line.id}>
                    <td>{line.producto_nombre}</td>
                    <td>{line.lote || "—"}</td>
                    <td>{line.fecha_vencimiento ? fecha(line.fecha_vencimiento) : "—"}</td>
                    <td className="money">{cantidad(line.cantidad, line.unidad)}</td>
                  </tr>
                ))}
                {!load || load.lineas.length === 0 ? (
                  <tr>
                    <td colSpan={4}>{load ? "Esta carga todavía no lleva producto." : "No hay carga para este vehículo en esa fecha."}</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
        {canLoad ? (
          <div>
            {!load ? (
              <button type="button" className="button" onClick={openLoad} disabled={!vehicleId}>
                Abrir carga
              </button>
            ) : (
              <form className="user-form" onSubmit={addLine}>
                <h2>Agregar de bodega</h2>
                <label>
                  Existencia
                  <select required value={existenciaId} onChange={(event) => setExistenciaId(event.target.value)}>
                    <option value="">Elige un lote</option>
                    {stock.map((row) => (
                      <option key={row.id} value={row.id}>
                        {row.producto_nombre}
                        {row.lote ? ` · ${row.lote}` : ""} · {cantidad(row.cantidad, row.unidad)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Cantidad
                  <input required inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0" />
                </label>
                <button type="submit" className="button">
                  Cargar
                </button>
              </form>
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}
