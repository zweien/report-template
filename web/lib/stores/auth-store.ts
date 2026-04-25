import { create } from "zustand";
import api from "@/lib/api";

interface User {
  id: string;
  username: string;
}

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoading: true,

  login: async (username, password) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("token", data.access_token);
    const { data: user } = await api.get("/auth/me");
    set({ user });
  },

  register: async (username, password) => {
    await api.post("/auth/register", { username, password });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null });
  },

  checkAuth: async () => {
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
}));
