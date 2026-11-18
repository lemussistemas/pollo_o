import { createContext } from "react"

import type { AccessLevel, User } from "../types.ts"

export type AuthValue = {
  user: User | null
  ready: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  can: (code: string, minimum?: AccessLevel) => boolean
}

export const AuthContext = createContext<AuthValue | null>(null)
