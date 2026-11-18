import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import type { Role, User } from "../types.ts"

type Draft = {
  id: number | null
  username: string
  password: string
  confirm: string
  first_name: string
  last_name: string
  email: string
  phone: string
  role_id: string
  is_active: boolean
}

const EMPTY: Draft = {
  id: null,
  username: "",
  password: "",
  confirm: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  role_id: "",
  is_active: true,
}

function draftFrom(user: User): Draft {
  return {
    id: user.id,
    username: user.username,
    password: "",
    confirm: "",
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    phone: user.phone,
    role_id: user.role ? String(user.role.id) : "",
    is_active: user.is_active,
  }
}

export function UsersPage() {
  const { user: actor, can, refreshUser } = useAuth()
  const canManage = can("usuarios.gestionar", "operate")
  const allowed = can("usuarios.ver") || canManage
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [query, setQuery] = useState("")
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [pending, setPending] = useState(false)

  async function load() {
    const [nextUsers, nextRoles] = await Promise.all([
      api<User[]>("/api/usuarios/"),
      api<Role[]>("/api/roles/"),
    ])
    setUsers(nextUsers)
    setRoles(nextRoles)
  }

  useEffect(() => {
    if (!allowed) return
    let cancel = false
    Promise.all([api<User[]>("/api/usuarios/"), api<Role[]>("/api/roles/")])
      .then(([nextUsers, nextRoles]) => {
        if (cancel) return
        setUsers(nextUsers)
        setRoles(nextRoles)
      })
      .catch((cause: unknown) => {
        if (cancel) return
        setError(cause instanceof ApiError ? cause.message : "No se pudieron cargar los usuarios.")
      })
    return () => {
      cancel = true
    }
  }, [allowed])

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setNotice("")
    if (draft.password !== draft.confirm) {
      setError("La confirmación de la contraseña no coincide.")
      return
    }
    if (!draft.id && draft.password.length < 8) {
      setError("La contraseña necesita al menos 8 caracteres.")
      return
    }
    setPending(true)
    const payload: Record<string, unknown> = {
      first_name: draft.first_name,
      last_name: draft.last_name,
      email: draft.email,
      phone: draft.phone,
      role_id: Number(draft.role_id),
      is_active: draft.is_active,
    }
    if (draft.password) payload.password = draft.password
    try {
      if (draft.id) {
        const updated = await api<User>(`/api/usuarios/${draft.id}/`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        })
        if (updated.id === actor?.id) await refreshUser()
        setNotice(`Se actualizó a ${updated.full_name}.`)
        setDraft(draftFrom(updated))
      } else {
        const created = await api<User>("/api/usuarios/", {
          method: "POST",
          body: JSON.stringify({ ...payload, username: draft.username }),
        })
        setNotice(`Se creó el usuario ${created.username}.`)
        setDraft(EMPTY)
      }
      await load()
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No se pudo guardar el usuario.")
    } finally {
      setPending(false)
    }
  }

  if (!allowed) return <Navigate to="/" replace />

  const needle = query.trim().toLowerCase()
  const visible = users.filter((item) => {
    if (!needle) return true
    const haystack = `${item.username} ${item.full_name} ${item.role?.name ?? ""}`.toLowerCase()
    return haystack.includes(needle)
  })
  const selectedRole = roles.find((role) => String(role.id) === draft.role_id)

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Accesos</p>
          <h1>Usuarios</h1>
          <p className="lede">Cada persona tiene un solo rol. El mismo usuario servirá luego en la tablet del vendedor.</p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="ok">{notice}</p> : null}
      <div className={canManage ? "users-layout" : "users-layout single"}>
        <section>
          <div className="toolbar">
            <label className="search">
              Buscar
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre, usuario o rol" />
            </label>
            {canManage ? (
              <button type="button" className="button button-secondary" onClick={() => setDraft(EMPTY)}>
                Nuevo usuario
              </button>
            ) : (
              <p className="section-note">Puedes consultar la lista. Solo gerencia crea y edita usuarios.</p>
            )}
          </div>
          <div className="table-wrap">
            <table>
              <caption>Personas con acceso</caption>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Usuario</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  {canManage ? <th></th> : null}
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.id} className={item.is_active ? undefined : "muted-row"}>
                    <td>
                      {item.full_name}
                      {item.phone ? <span className="cell-sub">{item.phone}</span> : null}
                    </td>
                    <td>{item.username}</td>
                    <td>{item.role?.name ?? "Sin rol"}</td>
                    <td>{item.is_active ? "Activo" : "Inactivo"}</td>
                    {canManage ? (
                      <td>
                        <button type="button" className="button button-quiet" onClick={() => setDraft(draftFrom(item))}>
                          Editar
                        </button>
                      </td>
                    ) : null}
                  </tr>
                ))}
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={canManage ? 5 : 4}>Nadie coincide con esa búsqueda.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
        {canManage ? (
          <form className="user-form" onSubmit={onSubmit}>
            <h2>{draft.id ? "Editar usuario" : "Nuevo usuario"}</h2>
            <label>
              Usuario
              <input
                value={draft.username}
                onChange={(event) => update("username", event.target.value)}
                required
                disabled={draft.id !== null}
                autoComplete="off"
              />
            </label>
            <div className="split">
              <label>
                Nombre
                <input
                  value={draft.first_name}
                  onChange={(event) => update("first_name", event.target.value)}
                  required
                />
              </label>
              <label>
                Apellido
                <input
                  value={draft.last_name}
                  onChange={(event) => update("last_name", event.target.value)}
                  required
                />
              </label>
            </div>
            <label>
              Rol
              <select value={draft.role_id} onChange={(event) => update("role_id", event.target.value)} required>
                <option value="">Elige un rol</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>
            {selectedRole ? <p className="section-note">{selectedRole.summary}</p> : null}
            {selectedRole?.code === "vendedor" ? (
              <p className="section-note">Este usuario es el que va a entrar en la tablet con impresora.</p>
            ) : null}
            <label>
              Teléfono
              <input value={draft.phone} onChange={(event) => update("phone", event.target.value)} />
            </label>
            <label>
              Correo
              <input
                type="email"
                value={draft.email}
                onChange={(event) => update("email", event.target.value)}
              />
            </label>
            <label>
              {draft.id ? "Nueva contraseña" : "Contraseña"}
              <input
                type="password"
                autoComplete="new-password"
                value={draft.password}
                onChange={(event) => update("password", event.target.value)}
                required={!draft.id}
                placeholder={draft.id ? "Déjala en blanco para no cambiarla" : ""}
              />
            </label>
            <label>
              Confirmar contraseña
              <input
                type="password"
                autoComplete="new-password"
                value={draft.confirm}
                onChange={(event) => update("confirm", event.target.value)}
                required={!draft.id || draft.password.length > 0}
              />
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={(event) => update("is_active", event.target.checked)}
              />
              Usuario activo
            </label>
            <p className="section-note">Tiene que quedar al menos una persona activa en gerencia.</p>
            <button className="button" type="submit" disabled={pending}>
              {pending ? "Guardando…" : "Guardar"}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  )
}
