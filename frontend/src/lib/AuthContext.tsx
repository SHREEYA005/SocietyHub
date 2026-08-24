import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api, setToken, clearToken, hasToken } from './api'
import type { UserOut } from './types'

interface AuthContextValue {
  user: UserOut | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, flatNumber: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!hasToken()) {
      setLoading(false)
      return
    }
    api.get<UserOut>('/auth/me')
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const res = await api.post<{ access_token: string; user: UserOut }>('/auth/login', { email, password })
    setToken(res.access_token)
    setUser(res.user)
  }

  async function register(name: string, email: string, password: string, flatNumber: string) {
    const res = await api.post<{ access_token: string; user: UserOut }>('/auth/register', {
      name, email, password, flat_number: flatNumber || undefined,
    })
    setToken(res.access_token)
    setUser(res.user)
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
