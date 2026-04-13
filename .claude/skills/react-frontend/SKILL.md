---
name: react-frontend
description: React 19 + TypeScript frontend patterns for ProjeX Suite. Use when creating components, pages, hooks, stores, or API service layers. Covers Zustand state, React Query, TipTap editor, @dnd-kit drag-drop.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# React Frontend Patterns

## Component Template

```tsx
// src/components/{ComponentName}.tsx
import { useState } from "react";

interface {ComponentName}Props {
  title: string;
  onAction?: () => void;
}

export function {ComponentName}({ title, onAction }: {ComponentName}Props) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
    </div>
  );
}
```

## Zustand Store Template

```tsx
// src/stores/{module}Store.ts
import { create } from "zustand";

interface {Module}State {
  items: {Module}Item[];
  isLoading: boolean;
  setItems: (items: {Module}Item[]) => void;
  addItem: (item: {Module}Item) => void;
  updateItem: (id: string, patch: Partial<{Module}Item>) => void;
}

export const use{Module}Store = create<{Module}State>((set) => ({
  items: [],
  isLoading: false,
  setItems: (items) => set({ items }),
  addItem: (item) => set((s) => ({ items: [...s.items, item] })),
  updateItem: (id, patch) =>
    set((s) => ({
      items: s.items.map((i) => (i.id === id ? { ...i, ...patch } : i)),
    })),
}));
```

## React Query API Hook Template

```tsx
// src/hooks/use{Module}.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";

export function use{Module}s(spaceKey: string) {
  return useQuery({
    queryKey: ["{module}s", spaceKey],
    queryFn: () => api.get(`/spaces/${spaceKey}/items`).then((r) => r.data.data),
  });
}

export function useCreate{Module}() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Create{Module}Request) =>
      api.post(`/spaces/${data.spaceKey}/items`, data).then((r) => r.data.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["{module}s", vars.spaceKey] });
    },
  });
}
```

## API Client

```tsx
// src/services/api.ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      try {
        const refresh = localStorage.getItem("refresh_token");
        const { data } = await axios.post("/api/v1/auth/refresh", { refresh_token: refresh });
        localStorage.setItem("access_token", data.data.access_token);
        error.config.headers.Authorization = `Bearer ${data.data.access_token}`;
        return axios(error.config);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
```

## Page Layout Template

```tsx
// src/pages/{Module}Page.tsx
import { useParams } from "react-router-dom";
import { use{Module}s } from "@/hooks/use{Module}";

export default function {Module}Page() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const { data, isLoading, error } = use{Module}s(spaceKey!);

  if (isLoading) return <div className="flex items-center justify-center h-64"><Spinner /></div>;
  if (error) return <ErrorBanner message={error.message} />;

  return (
    <div className="flex flex-col gap-4 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{spaceKey} — {Module}</h1>
        <Button onClick={() => {/* open create modal */}}>+ Create</Button>
      </header>
      <main>{/* render content */}</main>
    </div>
  );
}
```

## CRITICAL RULES
- ALWAYS use TypeScript strict mode — no `any`
- ALWAYS use interfaces over types for object shapes
- ALWAYS use Zustand for client state, React Query for server state
- NEVER prop-drill more than 2 levels — use stores
- ALWAYS implement optimistic updates for drag-drop operations
- ALWAYS add error boundaries around major page sections
- ALWAYS include aria-labels on interactive elements
