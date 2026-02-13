import { create } from "zustand";
import { AuthApiError, type AuthUser, authApi } from "@/src/services/authApi";

type AuthState = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isBootstrapped: boolean;
  error: string | null;
  register: (email: string, password: string) => Promise<boolean>;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  bootstrapSession: () => Promise<void>;
  clearError: () => void;
};

const authTokenStorageKey = "auth_token";

function readStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(authTokenStorageKey);
}

function writeStoredToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(authTokenStorageKey, token);
}

function clearStoredToken() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(authTokenStorageKey);
}

function normalizeAuthError(error: unknown) {
  if (error instanceof AuthApiError) {
    if (error.status === 401) {
      return "Credenciales invalidas.";
    }

    if (error.status === 422) {
      return "Revisa los datos enviados.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "No fue posible completar la operacion.";
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  isBootstrapped: false,
  error: null,
  register: async (email, password) => {
    set({ isLoading: true, error: null });

    try {
      const tokens = await authApi.register({ email, password });
      const user = await authApi.me(tokens.access_token);

      writeStoredToken(tokens.access_token);

      set({
        user,
        token: tokens.access_token,
        isAuthenticated: true,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });

      return true;
    } catch (error) {
      clearStoredToken();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        isBootstrapped: true,
        error: normalizeAuthError(error)
      });

      return false;
    }
  },
  login: async (email, password) => {
    set({ isLoading: true, error: null });

    try {
      const tokens = await authApi.login({ email, password });
      const user = await authApi.me(tokens.access_token);

      writeStoredToken(tokens.access_token);

      set({
        user,
        token: tokens.access_token,
        isAuthenticated: true,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });

      return true;
    } catch (error) {
      clearStoredToken();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        isBootstrapped: true,
        error: normalizeAuthError(error)
      });

      return false;
    }
  },
  logout: async () => {
    set({ isLoading: true, error: null });

    const storedToken = readStoredToken();

    try {
      if (storedToken) {
        await authApi.logout(storedToken);
      }
    } catch {
      // Ignore API errors: local session must always be cleared.
    } finally {
      clearStoredToken();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });
    }
  },
  bootstrapSession: async () => {
    const storedToken = readStoredToken();

    if (!storedToken) {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const user = await authApi.me(storedToken);
      set({
        user,
        token: storedToken,
        isAuthenticated: true,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });
    } catch {
      clearStoredToken();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        isBootstrapped: true,
        error: null
      });
    }
  },
  clearError: () => set({ error: null })
}));
