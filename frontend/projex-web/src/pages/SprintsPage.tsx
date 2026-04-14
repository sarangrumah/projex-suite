import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Modal } from "@/components/Modal";

interface SprintItem {
  id: string; name: string; goal: string | null; status: string;
  start_date: string | null; end_date: string | null; item_count?: number;
}

const statusColors: Record<string, string> = {
  planned: "bg-slate-100 text-slate-600",
  active: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
};

export default function SprintsPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");

  const { data: sprints, isLoading } = useQuery({
    queryKey: ["sprints", spaceKey],
    queryFn: async () => (await api.get(`/spaces/${spaceKey}/sprints`)).data.data as SprintItem[],
    enabled: !!spaceKey,
  });

  const { data: backlog } = useQuery({
    queryKey: ["backlog", spaceKey],
    queryFn: async () => (await api.get(`/spaces/${spaceKey}/backlog`)).data,
    enabled: !!spaceKey,
  });

  const createSprint = useMutation({
    mutationFn: async () => { await api.post(`/spaces/${spaceKey}/sprints`, { name, goal: goal || undefined }); },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sprints", spaceKey] }); setShowCreate(false); setName(""); setGoal(""); },
  });

  const startSprint = useMutation({
    mutationFn: async (id: string) => { await api.post(`/sprints/${id}/start`); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sprints", spaceKey] }),
  });

  const closeSprint = useMutation({
    mutationFn: async (id: string) => { await api.post(`/sprints/${id}/close`); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sprints", spaceKey] }),
  });

  return (
    <div className="p-6 max-w-4xl">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Sprints</h1>
        <button onClick={() => setShowCreate(true)}
          className="rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors">
          + New Sprint
        </button>
      </header>

      {isLoading && <div className="flex justify-center h-32"><div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" /></div>}

      {/* Backlog count */}
      {backlog && (
        <div className="rounded-lg border border-slate-200 bg-white p-4 mb-4">
          <span className="text-sm text-text-muted">Backlog: </span>
          <span className="text-sm font-semibold text-text-primary">{backlog.meta.total} items</span>
          <span className="text-xs text-text-muted ml-1">not assigned to any sprint</span>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {sprints?.map((s) => (
          <div key={s.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-text-primary">{s.name}</h3>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[s.status]}`}>
                    {s.status}
                  </span>
                </div>
                {s.goal && <p className="text-xs text-text-muted mt-1">{s.goal}</p>}
                <div className="flex gap-3 mt-2 text-xs text-text-muted">
                  {s.start_date && <span>Start: {s.start_date}</span>}
                  {s.end_date && <span>End: {s.end_date}</span>}
                  {s.item_count !== undefined && <span>{s.item_count} items</span>}
                </div>
              </div>
              <div className="flex gap-2">
                {s.status === "planned" && (
                  <button onClick={() => startSprint.mutate(s.id)}
                    className="rounded-md bg-status-success px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 transition-colors">
                    Start
                  </button>
                )}
                {s.status === "active" && (
                  <button onClick={() => closeSprint.mutate(s.id)}
                    className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-slate-50 transition-colors">
                    Close
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {sprints && sprints.length === 0 && (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-text-muted text-sm">
            No sprints yet
          </div>
        )}
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Sprint">
        <form onSubmit={(e) => { e.preventDefault(); createSprint.mutate(); }} className="flex flex-col gap-3">
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Sprint name" required autoFocus
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Sprint goal (optional)" rows={2}
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowCreate(false)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={createSprint.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Create</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
