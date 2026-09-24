import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { fetchMe, login as apiLogin, logout as apiLogout, register as apiRegister } from "../api/auth";
import type { LoginData, RegisterData } from "../api/auth";
import { getToken, setToken } from "../api/client";
import type { User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  status: "loading" | "anon" | "authenticated";
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");

  const restore = useCallback(async () => {
    if (!getToken()) {
      setStatus("anon");
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
      setStatus("authenticated");
    } catch {
      setUser(null);
      setStatus("anon");
    }
  }, []);

  useEffect(() => {
    void restore();
  }, [restore]);

  const login = useCallback(async (data: LoginData) => {
    const token = await apiLogin(data);
    setToken(token.access_token);
    const me = await fetchMe();
    setUser(me);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    await apiRegister(data);
    const token = await apiLogin({ email: data.email, password: data.password });
    setToken(token.access_token);
    const me = await fetchMe();
    setUser(me);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // se continúa aunque la API no responda
    }
    setToken(null);
    setUser(null);
    setStatus("anon");
  }, []);

  const value = useMemo(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  }
  return context;
}