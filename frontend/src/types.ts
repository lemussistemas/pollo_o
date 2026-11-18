export type AccessLevel = "none" | "view" | "own" | "operate" | "full"

export type Grant = {
  code: string
  module: string
  module_label: string
  name: string
  description: string
  level: AccessLevel
  level_label: string
  sort_order: number
}

export type RoleBrief = {
  id: number
  code: string
  name: string
  summary: string
}

export type Role = RoleBrief & {
  description: string
  sort_order: number
  active_users: number
  permissions: Grant[]
}

export type User = {
  id: number
  username: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string
  is_active: boolean
  role: RoleBrief | null
  permissions: Grant[]
  last_login: string | null
  date_joined: string
}

export type FlowStep = {
  order: number
  code: string
  title: string
  detail: string
  participa: boolean
  nivel: AccessLevel
  nivel_label: string
}

export type Sistema = {
  nombre: string
  puntos_de_venta: number
  politica_devolucion: string
  flujo: FlowStep[]
}

export type LoginResponse = {
  access: string
  refresh: string
  user: User
}

const RANK: Record<AccessLevel, number> = {
  none: 0,
  view: 1,
  own: 2,
  operate: 3,
  full: 4,
}

export function allows(level: AccessLevel | undefined, minimum: AccessLevel) {
  return RANK[level ?? "none"] >= RANK[minimum]
}
