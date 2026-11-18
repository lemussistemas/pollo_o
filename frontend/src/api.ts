import type { LoginResponse } from "./types.ts"

export const ACCESS_KEY = "pollo_access"
export const REFRESH_KEY = "pollo_refresh"

const FIELD_LABELS: Record<string, string> = {
  username: "Usuario",
  password: "Contraseña",
  first_name: "Nombre",
  last_name: "Apellido",
  email: "Correo",
  phone: "Teléfono",
  role_id: "Rol",
  is_active: "Estado",
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function messageFrom(value: unknown): string {
  if (typeof value === "string") return value
  if (Array.isArray(value)) return value.map(messageFrom).filter(Boolean).join(" ")
  if (value && typeof value === "object") return formatApiError(value)
  return ""
}

export function formatApiError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "No se pudo completar la acción."
  const data = payload as Record<string, unknown>
  if (typeof data.detail === "string") return data.detail
  const parts: string[] = []
  for (const [key, value] of Object.entries(data)) {
    const text = messageFrom(value)
    if (!text) continue
    const label = FIELD_LABELS[key]
    parts.push(label ? `${label}: ${text}` : text)
  }
  return parts.join(" ") || "No se pudo completar la acción."
}

let refreshPromise: Promise<string | null> | null = null

async function refreshAccess(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return null
  const response = await fetch("/api/auth/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
  if (!response.ok) return null
  const data = (await response.json()) as { access?: string; refresh?: string }
  if (!data.access) return null
  localStorage.setItem(ACCESS_KEY, data.access)
  if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh)
  return data.access
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const access = localStorage.getItem(ACCESS_KEY)
  if (access) headers.set("Authorization", `Bearer ${access}`)

  const response = await fetch(path, { ...init, headers })
  if (response.status === 401 && retry && !path.endsWith("/auth/login/")) {
    refreshPromise ??= refreshAccess().finally(() => {
      refreshPromise = null
    })
    const next = await refreshPromise
    if (next) return api<T>(path, init, false)
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    window.dispatchEvent(new Event("pollo:unauthorized"))
    throw new ApiError(401, "La sesión expiró. Entra de nuevo.")
  }

  const text = await response.text()
  const data = text ? (JSON.parse(text) as unknown) : null
  if (!response.ok) throw new ApiError(response.status, formatApiError(data))
  return data as T
}

export function saveSession(session: LoginResponse) {
  localStorage.setItem(ACCESS_KEY, session.access)
  localStorage.setItem(REFRESH_KEY, session.refresh)
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}
