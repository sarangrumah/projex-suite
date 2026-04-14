import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";

interface UserItem {
  id: string; email: string; display_name: string; role: string;
  mfa_enabled: boolean; is_active: boolean; last_login_at: string | null; created_at: string;
}

const roleColors: Record<string, string> = {
  admin: "bg-red-100 text-red-700", member: "bg-blue-100 text-blue-700",
  viewer: "bg-slate-100 text-slate-600", guest: "bg-amber-100 text-amber-700",
};

export default function UsersPage() {
  const qc = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await api.get("/admin/users/")).data as { data: UserItem[]; meta: { total: number } },
  });

  const updateUser = useMutation({
    mutationFn: async ({ id, role }: { id: string; role: string }) => {
      await api.put(`/admin/users/${id}`, { role });
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin-users"] }); setEditingId(null); },
  });

  const deactivateUser = useMutation({
    mutationFn: async (id: string) => { await api.delete(`/admin/users/${id}`); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  return (
    <div className="p-6">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-primary">User Management</h1>
        <span className="text-sm text-text-muted">{data?.meta.total ?? 0} users</span>
      </header>

      {isLoading && <div className="flex justify-center h-32"><div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" /></div>}

      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-surface-tertiary text-left text-xs text-text-muted">
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">MFA</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last Login</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.data.map((u) => (
              <tr key={u.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-3">
                  <p className="font-medium text-text-primary">{u.display_name}</p>
                  <p className="text-xs text-text-muted">{u.email}</p>
                </td>
                <td className="px-4 py-3">
                  {editingId === u.id ? (
                    <div className="flex items-center gap-1">
                      <select value={editRole} onChange={(e) => setEditRole(e.target.value)}
                        className="rounded border border-slate-200 px-2 py-1 text-xs">
                        {["admin", "member", "viewer", "guest"].map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                      <button onClick={() => updateUser.mutate({ id: u.id, role: editRole })}
                        className="text-xs text-brand-blue hover:underline">Save</button>
                      <button onClick={() => setEditingId(null)}
                        className="text-xs text-text-muted hover:underline">Cancel</button>
                    </div>
                  ) : (
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium cursor-pointer ${roleColors[u.role]}`}
                      onClick={() => { setEditingId(u.id); setEditRole(u.role); }}>
                      {u.role}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs ${u.mfa_enabled ? "text-status-success" : "text-text-muted"}`}>
                    {u.mfa_enabled ? "Enabled" : "Off"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 text-xs ${u.is_active ? "text-status-success" : "text-status-error"}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${u.is_active ? "bg-status-success" : "bg-status-error"}`} />
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-text-muted">
                  {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "Never"}
                </td>
                <td className="px-4 py-3 text-right">
                  {u.is_active && (
                    <button onClick={() => deactivateUser.mutate(u.id)}
                      className="text-xs text-status-error hover:underline">Deactivate</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
