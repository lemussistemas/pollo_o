import { useCallback, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"

import { ACCESS_KEY, api, clearSession, saveSession } from "../api.ts"
import { allows } from "../types.ts"
import type { AccessLevel, LoginResponse, User } from "../types.ts"
import { AuthContext } from "./context.ts"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(() => !localStorage.getItem(ACCESS_KEY))

  const refreshUser = useCallback(async () => {
    const next = await api<User>("/api/auth/me/")
    setUser(next)
  }, [])

  useEffect(() => {
    const onLost = () => setUser(null)
    window.addEventListener("pollo:unauthorized", onLost)
    return () => window.removeEventListener("pollo:unauthorized", onLost)
  }, [])

  useEffect(() => {
    if (!localStorage.getItem(ACCESS_KEY)) return
    let cancel = false
    api<User>("/api/auth/me/")
      .then((next) => {
        if (!cancel) setUser(next)
      })
      .catch(() => {
        clearSession()
      })
      .finally(() => {
        if (!cancel) setReady(true)
      })
    return () => {
      cancel = true
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    clearSession()
    const session = await api<LoginResponse>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username: username.trim(), password }),
    })
    saveSession(session)
    setUser(session.user)
  }, [])

  const logout = useCallback(() => {
    clearSession()
    setUser(null)
  }, [])

  const can = useCallback(
    (code: string, minimum: AccessLevel = "view") => {
      const grant = user?.permissions.find((item) => item.code === code)
      return allows(grant?.level, minimum)
    },
    [user],
  )

  const value = useMemo(
    () => ({ user, ready, login, logout, refreshUser, can }),
    [user, ready, login, logout, refreshUser, can],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
