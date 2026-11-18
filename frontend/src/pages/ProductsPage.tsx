import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { Page, Producto, ProductoOpciones } from "../types.ts"

const moneyFormat = new Intl.NumberFormat("es-HN", { style: "currency", currency: "HNL" })

function lempiras(value: string) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return value
  return moneyFormat.format(amount)
}

type Draft = {
  id?: number
  nombre: string
  unidad: string
  precio_base: string
  controla_lote: boolean
  activo: boolean
  notas: string
}

const emptyDraft: Draft = {
  nombre: "",
  unidad: "unidad",
  precio_base: "",
  controla_lote: false,
  activo: true,
  notas: "",
}

function draftFrom(product: Producto): Draft {
  return {
    id: product.id,
    nombre: product.nombre,
    unidad: product.unidad,
    precio_base: product.precio_base,
    controla_lote: product.controla_lote,
    activo: product.activo,
    notas: product.notas,
  }
}

export function ProductsPage() {
  const { can } = useAuth()
  const canEdit = can("productos.gestionar", "operate")
  const canPrice = can("productos.precios", "operate")
  const [options, setOptions] = useState<ProductoOpciones | null>(null)
  const [page, setPage] = useState<Page<Producto> | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [query, setQuery] = useState("")
  const [draft, setDraft] = useState<Draft>(emptyDraft)
  const [selected, setSelected] = useState<Producto | null>(null)
  const [clienteId, setClienteId] = useState("")
  const [precio, setPrecio] = useState("")
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    if (!can("productos.ver")) return
    let cancel = false
    api<ProductoOpciones>("/api/productos/opciones/")
      .then((next) => {
        if (!cancel) setOptions(next)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudo abrir el catálogo.")
      })
    return () => {
      cancel = true
    }
  }, [can])

  useEffect(() => {
    if (!can("productos.ver")) return
    let cancel = false
    const params = new URLSearchParams({ page: String(pageNumber) })
    if (query.trim()) params.set("q", query.trim())
    api<Page<Producto>>(`/api/productos/?${params.toString()}`)
      .then((next) => {
        if (!cancel) setPage(next)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudo leer el catálogo.")
      })
    return () => {
      cancel = true
    }
  }, [can, pageNumber, query, revision])

  if (!can("productos.ver")) return <Navigate to="/" replace />

  function search(event: FormEvent) {
    event.preventDefault()
    const form = new FormData(event.currentTarget as HTMLFormElement)
    setQuery(String(form.get("q") ?? ""))
    setPageNumber(1)
  }

  function choose(product: Producto) {
    setSelected(product)
    setError("")
    setNotice("")
    if (canEdit) setDraft(draftFrom(product))
  }

  async function saveProduct(event: FormEvent) {
    event.preventDefault()
    setError("")
    setNotice("")
    const body = {
      nombre: draft.nombre.trim(),
      unidad: draft.unidad,
      precio_base: draft.precio_base || "0",
      controla_lote: draft.controla_lote,
      activo: draft.activo,
      notas: draft.notas,
    }
    try {
      const saved = await api<Producto>(draft.id ? `/api/productos/${draft.id}/` : "/api/productos/", {
        method: draft.id ? "PATCH" : "POST",
        body: JSON.stringify(body),
      })
      setSelected(saved)
      setDraft(draftFrom(saved))
      setNotice(draft.id ? `Se actualizó ${saved.nombre}.` : `Se creó ${saved.nombre}.`)
      setQuery("")
      setPageNumber(1)
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo guardar el producto.")
    }
  }

  async function savePrice(event: FormEvent) {
    event.preventDefault()
    if (!selected) return
    setError("")
    setNotice("")
    try {
      const saved = await api<Producto>(`/api/productos/${selected.id}/precios/`, {
        method: "POST",
        body: JSON.stringify({ cliente_id: Number(clienteId), precio }),
      })
      setSelected(saved)
      setPrecio("")
      setNotice("El precio quedó guardado para ese cliente.")
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo guardar el precio.")
    }
  }

  async function removePrice(priceId: number) {
    if (!selected) return
    setError("")
    try {
      const saved = await api<Producto>(`/api/productos/${selected.id}/precios/${priceId}/`, { method: "DELETE" })
      setSelected(saved)
      setNotice("Ese cliente vuelve al precio de lista.")
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo quitar el precio.")
    }
  }

  const showPanel = canEdit || selected

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Catálogo</p>
          <h1>Productos</h1>
          <p className="lede">
            Inventario registra el producto por unidad o por libra. Si lleva lote y vencimiento, se pedirá al
            entrar a la bodega seca. El precio de lista es la base; facturación puede fijar otro para cada cliente.
          </p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="ok">{notice}</p> : null}
      <div className={showPanel ? "users-layout" : "users-layout single"}>
        <section>
          <form className="filters" onSubmit={search}>
            <label>
              Buscar
              <input name="q" placeholder="Nombre o código" defaultValue={query} />
            </label>
            <button type="submit" className="button">
              Buscar
            </button>
          </form>
          <div className="table-wrap">
            <table>
              <caption>{page ? `${page.count} productos` : "Productos"}</caption>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Unidad</th>
                  <th className="money">Lista</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(page?.results ?? []).map((product) => (
                  <tr key={product.id} className={product.activo ? undefined : "void"}>
                    <td>
                      {product.nombre}
                      <span className="perm-help">
                        {product.codigo}
                        {product.controla_lote ? " · Lote y vencimiento" : ""}
                        {product.precios.length ? ` · ${product.precios.length} precios` : ""}
                      </span>
                    </td>
                    <td>{product.unidad_label}</td>
                    <td className="money">{lempiras(product.precio_base)}</td>
                    <td>
                      <button type="button" className="button button-quiet" onClick={() => choose(product)}>
                        {canEdit ? "Editar" : "Ver"}
                      </button>
                    </td>
                  </tr>
                ))}
                {page && page.results.length === 0 ? (
                  <tr>
                    <td colSpan={4}>Todavía no hay productos. El Excel no traía los 157 ítems.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          {page && page.count > 25 ? (
            <div className="toolbar">
              <button
                type="button"
                className="button button-quiet"
                disabled={!page.previous}
                onClick={() => setPageNumber((current) => Math.max(1, current - 1))}
              >
                Anterior
              </button>
              <button
                type="button"
                className="button button-quiet"
                disabled={!page.next}
                onClick={() => setPageNumber((current) => current + 1)}
              >
                Siguiente
              </button>
            </div>
          ) : null}
        </section>
        {showPanel ? (
          <div>
            {canEdit ? (
              <form className="user-form" onSubmit={saveProduct}>
                <h2>{draft.id ? draft.nombre || "Producto" : "Nuevo producto"}</h2>
                <label>
                  Nombre
                  <input
                    required
                    value={draft.nombre}
                    onChange={(event) => setDraft({ ...draft, nombre: event.target.value })}
                  />
                </label>
                <label>
                  Unidad
                  <select value={draft.unidad} onChange={(event) => setDraft({ ...draft, unidad: event.target.value })}>
                    {(options?.unidades ?? []).map((unit) => (
                      <option key={unit.code} value={unit.code}>
                        {unit.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Precio de lista
                  <input
                    inputMode="decimal"
                    value={draft.precio_base}
                    onChange={(event) => setDraft({ ...draft, precio_base: event.target.value })}
                    placeholder="0.00"
                  />
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={draft.controla_lote}
                    onChange={(event) => setDraft({ ...draft, controla_lote: event.target.checked })}
                  />
                  Lleva lote y vencimiento
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={draft.activo}
                    onChange={(event) => setDraft({ ...draft, activo: event.target.checked })}
                  />
                  Producto activo
                </label>
                <label>
                  Notas
                  <textarea value={draft.notas} onChange={(event) => setDraft({ ...draft, notas: event.target.value })} />
                </label>
                <button type="submit" className="button">
                  Guardar producto
                </button>
                {draft.id ? (
                  <button
                    type="button"
                    className="button button-quiet"
                    onClick={() => {
                      setDraft(emptyDraft)
                      setSelected(null)
                    }}
                  >
                    Nuevo
                  </button>
                ) : null}
              </form>
            ) : null}
            {selected ? (
              <section className="equipment">
                <h2>Precio para cada cliente</h2>
                <p className="perm-help">
                  {selected.nombre} · lista {lempiras(selected.precio_base)}. Si un cliente no tiene precio propio, se
                  usa el de lista.
                </p>
                {selected.precios.length === 0 ? <p>Nadie tiene un precio distinto todavía.</p> : null}
                {selected.precios.length > 0 ? (
                  <ul>
                    {selected.precios.map((price) => (
                      <li key={price.id}>
                        {price.cliente_nombre} · {lempiras(price.precio)}
                        {canPrice ? (
                          <>
                            {" "}
                            <button type="button" className="button button-quiet" onClick={() => removePrice(price.id)}>
                              Quitar
                            </button>
                          </>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {canPrice ? (
                  <form className="equipment-form" onSubmit={savePrice}>
                    <label>
                      Cliente
                      <select required value={clienteId} onChange={(event) => setClienteId(event.target.value)}>
                        <option value="">Elige un cliente</option>
                        {(options?.clientes ?? []).map((client) => (
                          <option key={client.id} value={client.id}>
                            {client.nombre}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Precio
                      <input
                        required
                        inputMode="decimal"
                        value={precio}
                        onChange={(event) => setPrecio(event.target.value)}
                        placeholder="0.00"
                      />
                    </label>
                    <button type="submit" className="button">
                      Guardar precio
                    </button>
                  </form>
                ) : null}
              </section>
            ) : canEdit ? (
              <p className="perm-help">Guarda el producto para poder fijar el precio de un cliente.</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}
