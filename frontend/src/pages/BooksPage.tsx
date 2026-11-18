import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { CierreDiario, DocumentoVenta, LibroResumen, Page, ReporteMensual } from "../types.ts"

const moneyFormat = new Intl.NumberFormat("es-HN", { style: "currency", currency: "HNL" })

function lempiras(value: string) {
  const amount = Number(value)
  if (Number.isNaN(amount)) return value
  return moneyFormat.format(amount)
}

function fecha(value: string | null) {
  if (!value) return ""
  const [year, month, day] = value.slice(0, 10).split("-")
  return `${day}/${month}/${year}`
}

function MonthTable({
  caption,
  rows,
  months,
}: {
  caption: string
  rows: { id: number; nombre: string; meses: string[]; total: string }[]
  months: string[]
}) {
  return (
    <div className="table-wrap">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th>Nombre</th>
            {months.map((month) => (
              <th key={month} className="money">
                {month}
              </th>
            ))}
            <th className="money">Total</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.nombre}</td>
              {row.meses.map((amount, index) => (
                <td key={`${row.id}-${months[index]}`} className="money">
                  {lempiras(amount)}
                </td>
              ))}
              <td className="money">{lempiras(row.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function BooksPage() {
  const { can } = useAuth()
  const [resumen, setResumen] = useState<LibroResumen | null>(null)
  const [page, setPage] = useState<Page<DocumentoVenta> | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [query, setQuery] = useState("")
  const [caja, setCaja] = useState("")
  const [condicion, setCondicion] = useState("")
  const [estado, setEstado] = useState("")
  const [proveedores, setProveedores] = useState<ReporteMensual | null>(null)
  const [vendedores, setVendedores] = useState<ReporteMensual | null>(null)
  const [cierres, setCierres] = useState<{ total: string; cierres: CierreDiario[] } | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!can("contabilidad.libros")) return
    let cancel = false
    Promise.all([
      api<LibroResumen>("/api/libros/resumen/"),
      api<ReporteMensual>("/api/libros/proveedores/"),
      api<ReporteMensual>("/api/libros/vendedores/"),
      api<{ total: string; cierres: CierreDiario[] }>("/api/libros/cierres/"),
    ])
      .then(([summary, suppliers, sellers, closings]) => {
        if (cancel) return
        setResumen(summary)
        setProveedores(suppliers)
        setVendedores(sellers)
        setCierres(closings)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudieron abrir los libros.")
      })
    return () => {
      cancel = true
    }
  }, [can])

  useEffect(() => {
    if (!can("contabilidad.libros")) return
    let cancel = false
    const params = new URLSearchParams({ page: String(pageNumber) })
    if (query.trim()) params.set("q", query.trim())
    if (caja) params.set("caja", caja)
    if (condicion) params.set("condicion", condicion)
    if (estado) params.set("estado", estado)
    api<Page<DocumentoVenta>>(`/api/libros/documentos/?${params.toString()}`)
      .then((next) => {
        if (!cancel) setPage(next)
      })
      .catch((cause: unknown) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudo leer el libro de ventas.")
      })
    return () => {
      cancel = true
    }
  }, [can, pageNumber, query, caja, condicion, estado])

  if (!can("contabilidad.libros")) return <Navigate to="/" replace />

  function search(event: FormEvent) {
    event.preventDefault()
    const form = new FormData(event.currentTarget as HTMLFormElement)
    setQuery(String(form.get("q") ?? ""))
    setCaja(String(form.get("caja") ?? ""))
    setCondicion(String(form.get("condicion") ?? ""))
    setEstado(String(form.get("estado") ?? ""))
    setPageNumber(1)
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Contabilidad</p>
          <h1>Libro de ventas</h1>
          <p className="lede">
            {resumen?.razon_social || "Depósito"}
            {resumen?.desde && resumen.hasta ? ` · ${fecha(resumen.desde)} al ${fecha(resumen.hasta)}` : ""}.
            Los documentos salieron del Excel y quedaron en SQLite. Caja y oficina facturan cada una con su serie.
          </p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      {resumen ? (
        <section className="stats">
          <article className="stat">
            <span>Ventas netas</span>
            <strong>{lempiras(resumen.ventas_netas)}</strong>
          </article>
          <article className="stat">
            <span>Vigentes</span>
            <strong>{resumen.vigentes.toLocaleString("es-HN")}</strong>
          </article>
          <article className="stat">
            <span>Anulados</span>
            <strong>{resumen.anulados.toLocaleString("es-HN")}</strong>
          </article>
          <article className="stat">
            <span>Exentas</span>
            <strong>{lempiras(resumen.exentas)}</strong>
          </article>
          <article className="stat">
            <span>ISV 15%</span>
            <strong>{lempiras(resumen.isv_15)}</strong>
          </article>
          <article className="stat">
            <span>A crédito</span>
            <strong>{lempiras(resumen.credito.total)}</strong>
          </article>
        </section>
      ) : null}
      <form className="filters" onSubmit={search}>
        <label>
          Buscar
          <input name="q" placeholder="Cliente, RTN o número" defaultValue={query} />
        </label>
        <label>
          Caja
          <select name="caja" defaultValue={caja}>
            <option value="">Todas</option>
            {(resumen?.cajas ?? []).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label>
          Condición
          <select name="condicion" defaultValue={condicion}>
            <option value="">Todas</option>
            <option value="CONTADO">Contado</option>
            <option value="CREDITO">Crédito</option>
          </select>
        </label>
        <label>
          Estado
          <select name="estado" defaultValue={estado}>
            <option value="">Todos</option>
            <option value="VIGENTE">Vigente</option>
            <option value="ANULADO">Anulado</option>
          </select>
        </label>
        <button type="submit" className="button">
          Buscar
        </button>
      </form>
      <div className="table-wrap">
        <table>
          <caption>{page ? `${page.count.toLocaleString("es-HN")} documentos` : "Documentos"}</caption>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Documento</th>
              <th>Cliente</th>
              <th>Condición</th>
              <th className="money">Total</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {(page?.results ?? []).map((document) => (
              <tr key={document.id} className={document.estado === "ANULADO" ? "void" : undefined}>
                <td>{fecha(document.fecha)}</td>
                <td>
                  <strong>
                    {document.tipo} {document.numero}
                  </strong>
                  <span className="perm-help">
                    {document.caja} · {document.serie}
                  </span>
                </td>
                <td>
                  {document.cliente}
                  {document.rtn ? <span className="perm-help">RTN {document.rtn}</span> : null}
                </td>
                <td>{document.condicion === "CREDITO" ? "Crédito" : "Contado"}</td>
                <td className="money">{lempiras(document.total)}</td>
                <td>{document.estado === "ANULADO" ? "Anulado" : "Vigente"}</td>
              </tr>
            ))}
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
      {proveedores?.proveedores && proveedores.proveedores.length > 0 ? (
        <details className="book-section">
          <summary>Compras por proveedor</summary>
          <MonthTable caption="Año del reporte" rows={proveedores.proveedores} months={proveedores.meses} />
        </details>
      ) : null}
      {vendedores?.vendedores && vendedores.vendedores.length > 0 ? (
        <details className="book-section">
          <summary>Ventas por vendedor</summary>
          <MonthTable caption="Rutas del reporte" rows={vendedores.vendedores} months={vendedores.meses} />
        </details>
      ) : null}
      {cierres && cierres.cierres.length > 0 ? (
        <details className="book-section">
          <summary>Cierres diarios · {lempiras(cierres.total)}</summary>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Cierre</th>
                  <th>Facturas</th>
                  <th className="money">Libre</th>
                  <th className="money">Gravada</th>
                  <th className="money">Impuesto</th>
                  <th className="money">Total</th>
                </tr>
              </thead>
              <tbody>
                {cierres.cierres.map((closing) => (
                  <tr key={closing.id}>
                    <td>{fecha(closing.fecha)}</td>
                    <td>{closing.numero ?? closing.concepto}</td>
                    <td>
                      {closing.factura_desde}–{closing.factura_hasta}
                    </td>
                    <td className="money">{lempiras(closing.venta_libre)}</td>
                    <td className="money">{lempiras(closing.venta_gravada)}</td>
                    <td className="money">{lempiras(closing.impuesto)}</td>
                    <td className="money">{lempiras(closing.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </div>
  )
}
