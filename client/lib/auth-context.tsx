"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  api,
  clearToken,
  onAuthExpired,
  setToken,
} from "@/lib/api";
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
  let cancelled = false;

  async function initializeSession() {
    try {
      clearToken();

      const restoredToken = await api.restoreSession();

      if (!restoredToken) {
        if (!cancelled) {
          setUser(null);
        }

        return;
      }

      const currentUser = await api.me();

      if (!cancelled) {
        setUser(currentUser);
      }
    } catch {
      clearToken();

      if (!cancelled) {
        setUser(null);
      }
    } finally {
      if (!cancelled) {
        setIsLoading(false);
      }
    }
  }

  void initializeSession();

  return () => {
    cancelled = true;
  };
}, []);

  useEffect(() => {
    return onAuthExpired(() => setUser(null));
  }, []);

async function login(email: string, password: string) {
  const { access_token } = await api.login({
    email,
    password,
  });

  setToken(access_token);
  setUser(await api.me());
}

  async function register(fullName: string, email: string, password: string) {
    await api.register({ full_name: fullName, email, password });
  }

  function logout() {
  void api.logout().finally(() => {
    clearToken();
    setUser(null);
  });
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
