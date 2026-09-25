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
  login: (
    email: string,
    password: string,
  ) => Promise<void>;
  register: (
    fullName: string,
    email: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
  logoutAll: () => Promise<void>;
  changePassword: (
    currentPassword: string,
    newPassword: string,
  ) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
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
    return onAuthExpired(() => {
      setUser(null);
    });
  }, []);

  async function login(
    email: string,
    password: string,
  ): Promise<void> {
    const { access_token } = await api.login({
      email,
      password,
    });

    setToken(access_token);
    setUser(await api.me());
  }

  async function register(
    fullName: string,
    email: string,
    password: string,
  ): Promise<void> {
    await api.register({
      full_name: fullName,
      email,
      password,
    });
  }

  function logout(): void {
    void api.logout().finally(() => {
      clearToken();
      setUser(null);
    });
  }

  async function logoutAll(): Promise<void> {
    await api.logoutAll();

    clearToken();
    setUser(null);
  }

  async function changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<void> {
    await api.changePassword({
      currentPassword,
      newPassword,
    });

    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        register,
        logout,
        logoutAll,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an AuthProvider",
    );
  }

  return context;
}