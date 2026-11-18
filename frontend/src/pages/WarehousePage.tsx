import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { BodegaProducto, Existencia, MovimientoBodega, Page } from "../types.ts"

function fecha(value: string | null) {
  if (!value) return ""
  const [year, month, day] = value.slice(0, 10).split("-")
  return `${day}/${month}/${year}`
}

function cantidad(value: string, unidad: string) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${value} ${unidad}`
  const text = amount.toLocaleString("es-HN", { maximumFractionDigits: 3 })
  return `${text} ${unidad === "libra" ? "lb" : "und"}`
}

export function WarehousePage() {
  const { can } = useAuth()
  const canEnter = can("inventario.ingreso", "operate")
  const canDamage = can("inventario.mal_estado", "operate")
  const [products, setProducts] = useState<BodegaProducto[]>([])
  const [stock, setStock] = useState<Existencia[]>([])
  const [moves, setMoves] = useState<MovimientoBodega[]>([])
  const [productoId, setProductoId] = useState("")
  const [tipo, setTipo] = useState("ingreso")
  const [amount, setAmount] = useState("")
  const [lote, setLote] = useState("")
  const [vence, setVence] = useState("")
  const [nota, setNota] = useState("")
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [revision, setRevision] = useState(0)

  const selected = products.find((product) => String(product.id) === productoId)

  useEffect(() => {
    if (!can("inventario.ingreso")) return
    let cancel = false
    Promise.all([
      api<{ productos: BodegaProducto[] }>("/api/bodega/opciones/"),
      api<Existencia[]>("/api/bodega/existencias/"),
      api<Page<MovimientoBodega>>("/api/bodega/movimientos/"),
    ])
      .then(([options, rows, history]) => {
        if (cancel) return
        setProducts(options.productos)
        setStock(rows)
        setMoves(history.results)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudo abrir la bodega.")
      })
    return () => {
      cancel = true
    }
  }, [can, revision])

  if (!can("inventario.ingreso")) return <Navigate to="/" replace />

  async function save(event: FormEvent) {
    event.preventDefault()
    setError("")
    setNotice("")
    const body: Record<string, string> = {
      tipo,
      producto_id: productoId,
      cantidad: amount,
      nota,
    }
    if (selected?.controla_lote) {
      body.lote = lote.trim()
      body.fecha_vencimiento = vence
    }
    try {
      const saved = await api<MovimientoBodega>("/api/bodega/movimientos/", {
        method: "POST",
        body: JSON.stringify(body),
      })
      setAmount("")
      setLote("")
      setVence("")
      setNota("")
      setNotice(
        saved.tipo === "ingreso"
          ? `Entraron ${cantidad(saved.cantidad, saved.unidad_label === "Libra" ? "libra" : "unidad")} de ${saved.producto_nombre}.`
          : `Salió lo dañado de ${saved.producto_nombre}.`,
      )
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo registrar el movimiento.")
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Bodega seca</p>
          <h1>Entrada de producto</h1>
          <p className="lede">
            Aquí entra lo que llega a la bodega. Si el producto lleva lote, el vencimiento es obligatorio. Lo dañado
            no abre otro registro: se le da salida y baja la existencia.
          </p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="ok">{notice}</p> : null}
      <div className={canEnter ? "users-layout" : "users-layout single"}>
        <section>
          <div className="table-wrap">
            <table>
              <caption>{stock.length} existencias</caption>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Lote</th>
                  <th>Vence</th>
                  <th className="money">Cantidad</th>
                </tr>
              </thead>
              <tbody>
                {stock.map((row) => (
                  <tr key={row.id}>
                    <td>
                      {row.producto_nombre}
                      <span className="perm-help">{row.producto_codigo}</span>
                    </td>
                    <td>{row.lote || "—"}</td>
                    <td>{row.fecha_vencimiento ? fecha(row.fecha_vencimiento) : "—"}</td>
                    <td className="money">{cantidad(row.cantidad, row.unidad)}</td>
                  </tr>
                ))}
                {stock.length === 0 ? (
                  <tr>
                    <td colSpan={4}>La bodega todavía no tiene existencia.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          {moves.length > 0 ? (
            <div className="table-wrap stack-table">
              <table>
                <caption>Últimos movimientos</caption>
                <thead>
                  <tr>
                    <th>Movimiento</th>
                    <th>Producto</th>
                    <th className="money">Cantidad</th>
                  </tr>
                </thead>
                <tbody>
                  {moves.map((move) => (
                    <tr key={move.id} className={move.tipo === "salida_danado" ? "void" : undefined}>
                      <td>
                        {move.tipo_label}
                        <span className="perm-help">
                          {fecha(move.creado_en)}
                          {move.lote ? ` · ${move.lote}` : ""}
                          {move.nota ? ` · ${move.nota}` : ""}
                        </span>
                      </td>
                      <td>{move.producto_nombre}</td>
                      <td className="money">{cantidad(move.cantidad, move.unidad_label === "Libra" ? "libra" : "unidad")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
        {canEnter ? (
          <form className="user-form" onSubmit={save}>
            <h2>{tipo === "salida_danado" ? "Salida por dañado" : "Nuevo ingreso"}</h2>
            {canDamage ? (
              <label>
                Qué se registra
                <select value={tipo} onChange={(event) => setTipo(event.target.value)}>
                  <option value="ingreso">Ingreso a bodega</option>
                  <option value="salida_danado">Salida por dañado</option>
                </select>
              </label>
            ) : null}
            <label>
              Producto
              <select required value={productoId} onChange={(event) => setProductoId(event.target.value)}>
                <option value="">Elige un producto</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.nombre} · {product.unidad_label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Cantidad
              <input required inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0" />
            </label>
            {selected?.controla_lote ? (
              <>
                <label>
                  Lote
                  <input required value={lote} onChange={(event) => setLote(event.target.value)} />
                </label>
                <label>
                  Vencimiento
                  <input required type="date" value={vence} onChange={(event) => setVence(event.target.value)} />
                </label>
              </>
            ) : null}
            <label>
              Nota
              <input value={nota} onChange={(event) => setNota(event.target.value)} />
            </label>
            <button type="submit" className="button">
              {tipo === "salida_danado" ? "Registrar salida" : "Registrar ingreso"}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  )
}
