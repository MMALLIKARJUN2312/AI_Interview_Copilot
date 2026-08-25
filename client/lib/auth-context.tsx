"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { api, clearToken, getToken, onAuthExpired, setTokens } from "@/lib/api";
import type { UserResponse } from "@/lib/types";

interface AuthContextValue {
  user: UserResponse | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    fullName: string,
    email: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getToken();

    const pending = token
      ? api.me().then(setUser).catch(() => {
          clearToken();
          setUser(null);
        })
      : Promise.resolve();

    pending.finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    return onAuthExpired(() => setUser(null));
  }, []);

  async function login(email: string, password: string) {
    const { access_token, refresh_token } = await api.login({ email, password });
    setTokens(access_token, refresh_token);
    setUser(await api.me());
  }

  async function register(fullName: string, email: string, password: string) {
    await api.register({ full_name: fullName, email, password });
  }

  function logout() {
    api.logout().catch(() => {
      // best-effort server-side revocation; local state is cleared regardless
    });
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);

  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return ctx;
}
