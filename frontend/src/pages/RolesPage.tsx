import { Fragment, useEffect, useState } from "react"

import { ApiError, api } from "../api.ts"
import { useAuth } from "../auth/useAuth.ts"
import { LevelPill } from "../components/LevelPill.tsx"
import type { Grant, Role } from "../types.ts"

type MatrixRow = {
  permission: Grant
  levels: Record<string, Grant | undefined>
}

type MatrixGroup = {
  module: string
  label: string
  rows: MatrixRow[]
}

function matrix(roles: Role[]): MatrixGroup[] {
  const first = roles[0]
  if (!first) return []
  const groups: MatrixGroup[] = []
  const ordered = [...first.permissions].sort((a, b) => a.sort_order - b.sort_order)
  for (const permission of ordered) {
    let group = groups.find((item) => item.module === permission.module)
    if (!group) {
      group = { module: permission.module, label: permission.module_label, rows: [] }
      groups.push(group)
    }
    const levels: Record<string, Grant | undefined> = {}
    for (const role of roles) {
      levels[role.code] = role.permissions.find((item) => item.code === permission.code)
    }
    group.rows.push({ permission, levels })
  }
  return groups
}

export function RolesPage() {
  const { user } = useAuth()
  const [roles, setRoles] = useState<Role[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    let cancel = false
    api<Role[]>("/api/roles/")
      .then((next) => {
        if (!cancel) setRoles(next)
      })
      .catch((cause) => {
        if (!cancel) setError(cause instanceof ApiError ? cause.message : "No se pudieron cargar los roles.")
      })
    return () => {
      cancel = true
    }
  }, [])

  const groups = matrix(roles)

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Quién hace qué</p>
          <h1>Cinco roles para un solo recorrido.</h1>
          <p className="lede">
            Gerencia asigna uno de estos roles. No se crean roles nuevos: cada persona entra a la parte
            del día que le toca.
          </p>
        </div>
      </header>
      {error ? (
        <p className="notice" role="alert">
          {error}
        </p>
      ) : null}
      <div className="role-grid">
        {roles.map((role) => (
          <article key={role.code} className={role.code === user?.role?.code ? "role-blurb mine" : "role-blurb"}>
            <header>
              <h2>{role.name}</h2>
              <span>{role.active_users} activos</span>
            </header>
            <p>{role.description}</p>
          </article>
        ))}
      </div>
      <div className="table-wrap">
        <table className="matrix">
          <caption>Permisos por rol</caption>
          <thead>
            <tr>
              <th>Permiso</th>
              {roles.map((role) => (
                <th key={role.code} className={role.code === user?.role?.code ? "mine" : undefined}>
                  {role.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {groups.map((group) => (
              <Fragment key={group.module}>
                <tr className="module-row">
                  <th colSpan={roles.length + 1}>{group.label}</th>
                </tr>
                {group.rows.map((row) => (
                  <tr key={row.permission.code}>
                    <th scope="row">
                      <span className="perm-name">{row.permission.name}</span>
                      <span className="perm-help">{row.permission.description}</span>
                    </th>
                    {roles.map((role) => {
                      const grant = row.levels[role.code]
                      return (
                        <td key={role.code} className={role.code === user?.role?.code ? "mine" : undefined}>
                          <LevelPill
                            level={grant?.level ?? "none"}
                            label={grant?.level_label ?? "Sin acceso"}
                          />
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
