import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate, useSearchParams } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { Cliente, ClienteOpciones, Equipo, Page } from "../types.ts"

type Draft = {
  id: number | null
  nombre: string
  rtn: string
  telefono: string
  direccion: string
  punto_id: string
  dia_ruta: string
  vendedor_id: string
  latitud: string
  longitud: string
  credito_habilitado: boolean
  limite_credito: string
  notas: string
  activo: boolean
  equipos: Equipo[]
}

const EMPTY: Draft = {
  id: null,
  nombre: "",
  rtn: "",
  telefono: "",
  direccion: "",
  punto_id: "",
  dia_ruta: "",
  vendedor_id: "",
  latitud: "",
  longitud: "",
  credito_habilitado: false,
  limite_credito: "",
  notas: "",
  activo: true,
  equipos: [],
}

function draftFrom(cliente: Cliente): Draft {
  return {
    id: cliente.id,
    nombre: cliente.nombre,
    rtn: cliente.rtn,
    telefono: cliente.telefono,
    direccion: cliente.direccion,
    punto_id: cliente.punto.id ? String(cliente.punto.id) : "",
    dia_ruta: cliente.dia_ruta,
    vendedor_id: cliente.vendedor ? String(cliente.vendedor.id) : "",
    latitud: cliente.latitud ?? "",
    longitud: cliente.longitud ?? "",
    credito_habilitado: cliente.credito_habilitado,
    limite_credito: cliente.limite_credito ?? "",
    notas: cliente.notas,
    activo: cliente.activo,
    equipos: cliente.equipos,
  }
}

function money(value: string | null) {
  if (!value) return ""
  return new Intl.NumberFormat("es-HN", { style: "currency", currency: "HNL" }).format(Number(value))
}

export function ClientsPage() {
  const { can } = useAuth()
  const allowed = can("clientes.ver")
  const canEdit = can("clientes.gestionar", "operate")
  const canCredit = can("clientes.credito", "operate")
  const [params] = useSearchParams()
  const [options, setOptions] = useState<ClienteOpciones | null>(null)
  const [page, setPage] = useState<Page<Cliente> | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [query, setQuery] = useState("")
  const [punto, setPunto] = useState("")
  const [onlyNew, setOnlyNew] = useState(params.get("nuevos") === "1")
  const [onlyCredit, setOnlyCredit] = useState(false)
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [equipo, setEquipo] = useState({ modelo: "", placa: "", ubicacion: "", foto: null as File | null })
  const [equipoTick, setEquipoTick] = useState(0)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [pending, setPending] = useState(false)

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  async function load(nextPage = pageNumber) {
    const search = new URLSearchParams()
    search.set("page", String(nextPage))
    if (query.trim()) search.set("q", query.trim())
    if (punto) search.set("punto", punto)
    if (onlyNew) search.set("nuevos", "1")
    if (onlyCredit) search.set("credito", "si")
    const [nextOptions, nextPageData] = await Promise.all([
      api<ClienteOpciones>("/api/clientes/opciones/"),
      api<Page<Cliente>>(`/api/clientes/?${search.toString()}`),
    ])
    setOptions(nextOptions)
    setPage(nextPageData)
    setPageNumber(nextPage)
  }

  useEffect(() => {
    if (!allowed) return
    let cancel = false
    load(1).catch((cause: unknown) => {
      if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudieron cargar los clientes.")
    })
    return () => {
      cancel = true
    }
    // The first load uses the initial filters, including the new-clients alert.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowed])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setNotice("")
    setPending(true)
    const payload: Record<string, unknown> = {
      nombre: draft.nombre,
      rtn: draft.rtn,
      telefono: draft.telefono,
      direccion: draft.direccion,
      punto_id: Number(draft.punto_id),
      dia_ruta: draft.dia_ruta,
      vendedor_id: draft.vendedor_id ? Number(draft.vendedor_id) : null,
      latitud: draft.latitud || null,
      longitud: draft.longitud || null,
      notas: draft.notas,
      activo: draft.activo,
    }
    if (canCredit) {
      payload.credito_habilitado = draft.credito_habilitado
      payload.limite_credito = draft.credito_habilitado ? draft.limite_credito : null
    }
    try {
      const saved = draft.id
        ? await api<Cliente>(`/api/clientes/${draft.id}/`, { method: "PATCH", body: JSON.stringify(payload) })
        : await api<Cliente>("/api/clientes/", { method: "POST", body: JSON.stringify(payload) })
      setDraft(draftFrom(saved))
      setNotice(draft.id ? `Se actualizó a ${saved.nombre}.` : `Se creó ${saved.nombre}.`)
      await load(1)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo guardar el cliente.")
    } finally {
      setPending(false)
    }
  }

  async function addEquipo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft.id) return
    setError("")
    setPending(true)
    const body = new FormData()
    body.set("modelo", equipo.modelo)
    body.set("placa", equipo.placa)
    body.set("ubicacion", equipo.ubicacion)
    if (equipo.foto) body.set("foto", equipo.foto)
    try {
      await api<Equipo>(`/api/clientes/${draft.id}/equipos/`, { method: "POST", body })
      const refreshed = await api<Cliente>(`/api/clientes/${draft.id}/`)
      setDraft(draftFrom(refreshed))
      setEquipo({ modelo: "", placa: "", ubicacion: "", foto: null })
      setEquipoTick((current) => current + 1)
      setNotice("Se agregó el equipo.")
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo guardar el equipo.")
    } finally {
      setPending(false)
    }
  }

  async function withdraw(item: Equipo) {
    if (!draft.id) return
    setError("")
    try {
      await api<Equipo>(`/api/clientes/${draft.id}/equipos/${item.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ estado: "retirado" }),
      })
      const refreshed = await api<Cliente>(`/api/clientes/${draft.id}/`)
      setDraft(draftFrom(refreshed))
      setNotice(`Se retiró ${item.modelo}. La ubicación quedó cerrada.`)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo retirar el equipo.")
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Cartera</p>
          <h1>Clientes</h1>
          <p className="lede">
            Facturación y admin registran al cliente, su equipo y su ubicación. El crédito lo autoriza gerencia,
            y no es para todos. El abono parcial se aplicará cuando existan las facturas.
          </p>
        </div>
      </header>
      {options && options.nuevos > 0 ? (
        <p className="ok">
          {options.nuevos} {options.nuevos === 1 ? "cliente nuevo" : "clientes nuevos"} en los últimos 7 días.
        </p>
      ) : null}
      {error ? <p className="notice" role="alert">{error}</p> : null}
      {notice ? <p className="ok">{notice}</p> : null}
      <div className={canEdit ? "users-layout" : "users-layout single"}>
        <section>
          <form
            className="toolbar"
            onSubmit={(event) => {
              event.preventDefault()
              load(1).catch((cause: unknown) => {
                setError(cause instanceof ApiError ? cause.message : "No se pudo buscar.")
              })
            }}
          >
            <label className="search">
              Buscar
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre, RTN o teléfono" />
            </label>
            <label>
              Punto
              <select value={punto} onChange={(event) => setPunto(event.target.value)}>
                <option value="">Todos</option>
                {(options?.puntos ?? []).map((item) => (
                  <option key={item.code} value={item.id}>{item.name}</option>
                ))}
              </select>
            </label>
            <label className="check">
              <input type="checkbox" checked={onlyNew} onChange={(event) => setOnlyNew(event.target.checked)} />
              Nuevos
            </label>
            <label className="check">
              <input type="checkbox" checked={onlyCredit} onChange={(event) => setOnlyCredit(event.target.checked)} />
              Con crédito
            </label>
            <button className="button button-secondary" type="submit">Buscar</button>
          </form>
          <div className="table-wrap">
            <table>
              <caption>{page ? `${page.count} clientes` : "Clientes"}</caption>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Punto</th>
                  <th>Ruta</th>
                  <th>Crédito</th>
                  {canEdit ? <th></th> : null}
                </tr>
              </thead>
              <tbody>
                {(page?.results ?? []).map((cliente) => (
                  <tr key={cliente.id} className={cliente.activo ? undefined : "muted-row"}>
                    <td>
                      {cliente.nombre}
                      <span className="cell-sub">
                        {cliente.codigo}
                        {cliente.es_nuevo ? " · Nuevo" : ""}
                        {cliente.vendedor ? ` · ${cliente.vendedor.full_name}` : ""}
                      </span>
                    </td>
                    <td>{cliente.punto.name}</td>
                    <td>{cliente.dia_ruta_label || "Sin día"}</td>
                    <td>{cliente.credito_habilitado ? money(cliente.limite_credito) : "Sin crédito"}</td>
                    {canEdit ? (
                      <td>
                        <button type="button" className="button button-quiet" onClick={() => setDraft(draftFrom(cliente))}>
                          Editar
                        </button>
                      </td>
                    ) : null}
                  </tr>
                ))}
                {page && page.results.length === 0 ? (
                  <tr>
                    <td colSpan={canEdit ? 5 : 4}>No hay clientes con ese filtro.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          {page && page.count > 25 ? (
            <div className="toolbar">
              <button type="button" className="button button-quiet" disabled={!page.previous} onClick={() => load(pageNumber - 1)}>
                Anterior
              </button>
              <button type="button" className="button button-quiet" disabled={!page.next} onClick={() => load(pageNumber + 1)}>
                Siguiente
              </button>
            </div>
          ) : null}
        </section>
        {canEdit ? (
          <div>
          <form className="user-form" onSubmit={onSubmit}>
            <h2>{draft.id ? "Editar cliente" : "Nuevo cliente"}</h2>
            {draft.id ? (
              <button type="button" className="button button-quiet" onClick={() => setDraft(EMPTY)}>
                Otro cliente
              </button>
            ) : null}
            <label>
              Nombre
              <input value={draft.nombre} onChange={(event) => update("nombre", event.target.value)} required />
            </label>
            <div className="split">
              <label>
                RTN
                <input value={draft.rtn} onChange={(event) => update("rtn", event.target.value)} />
              </label>
              <label>
                Teléfono
                <input value={draft.telefono} onChange={(event) => update("telefono", event.target.value)} />
              </label>
            </div>
            <label>
              Dirección
              <input value={draft.direccion} onChange={(event) => update("direccion", event.target.value)} />
            </label>
            <label>
              Punto de venta
              <select value={draft.punto_id} onChange={(event) => update("punto_id", event.target.value)} required>
                <option value="">Elige un punto</option>
                {(options?.puntos ?? []).map((item) => (
                  <option key={item.code} value={item.id}>{item.name}</option>
                ))}
              </select>
            </label>
            <div className="split">
              <label>
                Día de ruta
                <select value={draft.dia_ruta} onChange={(event) => update("dia_ruta", event.target.value)}>
                  <option value="">Sin ruta fija</option>
                  {(options?.dias ?? []).map((day) => (
                    <option key={day.code} value={day.code}>{day.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Vendedor
                <select value={draft.vendedor_id} onChange={(event) => update("vendedor_id", event.target.value)}>
                  <option value="">Sin asignar</option>
                  {(options?.vendedores ?? []).map((seller) => (
                    <option key={seller.id} value={seller.id}>{seller.full_name}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="split">
              <label>
                Latitud
                <input value={draft.latitud} onChange={(event) => update("latitud", event.target.value)} inputMode="decimal" />
              </label>
              <label>
                Longitud
                <input value={draft.longitud} onChange={(event) => update("longitud", event.target.value)} inputMode="decimal" />
              </label>
            </div>
            <label>
              Notas
              <input value={draft.notas} onChange={(event) => update("notas", event.target.value)} />
            </label>
            <label className="check">
              <input type="checkbox" checked={draft.activo} onChange={(event) => update("activo", event.target.checked)} />
              Cliente activo
            </label>
            {canCredit ? (
              <>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={draft.credito_habilitado}
                    onChange={(event) => update("credito_habilitado", event.target.checked)}
                  />
                  Autorizar crédito
                </label>
                {draft.credito_habilitado ? (
                  <label>
                    Límite
                    <input
                      value={draft.limite_credito}
                      onChange={(event) => update("limite_credito", event.target.value)}
                      inputMode="decimal"
                      required
                    />
                  </label>
                ) : (
                  <p className="section-note">Sin esta autorización el cliente solo compra de contado.</p>
                )}
              </>
            ) : (
              <p className="section-note">
                {draft.credito_habilitado
                  ? `Crédito autorizado hasta ${money(draft.limite_credito)}. Solo gerencia puede cambiarlo.`
                  : "Este cliente no tiene crédito. Solo gerencia puede autorizarlo."}
              </p>
            )}
            <button className="button" type="submit" disabled={pending}>
              {pending ? "Guardando…" : "Guardar cliente"}
            </button>
          </form>
            {draft.id ? (
              <div className="equipment">
                <h2>Equipos</h2>
                {draft.equipos.length === 0 ? <p className="section-note">Todavía no hay equipo en este cliente.</p> : null}
                {draft.equipos.map((item) => (
                  <article key={item.id} className="role-blurb">
                    <header>
                      <h3>{item.modelo}</h3>
                      <span>{item.estado === "retirado" ? "Retirado" : "Instalado"}</span>
                    </header>
                    <p>
                      {item.placa ? `Placa ${item.placa}. ` : ""}
                      {item.ubicacion || "Sin ubicación"}
                      {item.ubicacion_bloqueada ? " · Ubicación cerrada" : ""}
                    </p>
                    {item.foto ? <img className="equipo-foto" src={item.foto} alt="" /> : null}
                    {item.estado === "instalado" ? (
                      <button type="button" className="button button-quiet" onClick={() => withdraw(item)}>
                        Retirar y cerrar ubicación
                      </button>
                    ) : null}
                  </article>
                ))}
                <form className="equipment-form" onSubmit={addEquipo}>
                  <label>
                    Modelo
                    <input value={equipo.modelo} onChange={(event) => setEquipo({ ...equipo, modelo: event.target.value })} required />
                  </label>
                  <label>
                    Placa
                    <input value={equipo.placa} onChange={(event) => setEquipo({ ...equipo, placa: event.target.value })} />
                  </label>
                  <label>
                    Dónde está
                    <input value={equipo.ubicacion} onChange={(event) => setEquipo({ ...equipo, ubicacion: event.target.value })} placeholder="Por ejemplo, Suyapa" />
                  </label>
                  <label>
                    Foto
                    <input
                      key={equipoTick}
                      type="file"
                      accept="image/*"
                      onChange={(event) => setEquipo({ ...equipo, foto: event.target.files?.[0] ?? null })}
                    />
                  </label>
                  <button className="button button-secondary" type="submit" disabled={pending}>Agregar equipo</button>
                </form>
              </div>
            ) : (
              <p className="section-note">Guarda el cliente para poder agregar la foto y la placa del equipo.</p>
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}
