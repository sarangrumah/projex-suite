import { create } from "zustand";
import { api } from "@/services/api";

interface UserInfo {
  id: string;
  email: string;
  display_name: string;
  role: string;
  mfa_enabled: boolean;
  permissions: string[];
}

interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string, tenantSlug: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string,
    tenantSlug: string,
  ) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"),
  isLoading: false,

  login: async (email, password, tenantSlug) => {
    set({ isLoading: true });
    try {
      const res = await api.post("/auth/login", {
        email,
        password,
        tenant_slug: tenantSlug,
      });
      const { tokens, user } = res.data.data;
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  register: async (email, password, displayName, tenantSlug) => {
    set({ isLoading: true });
    try {
      const res = await api.post("/auth/register", {
        email,
        password,
        display_name: displayName,
        tenant_slug: tenantSlug,
      });
      const { tokens, user } = res.data.data;
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchMe: async () => {
    try {
      const res = await api.get("/auth/me");
      set({ user: res.data.data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  },
}));
