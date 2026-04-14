import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Modal } from "@/components/Modal";

interface KeyResult {
  id: string;
  title: string;
  metric_type: string;
  current_value: number;
  target_value: number;
  start_value: number;
  unit: string | null;
  progress: number;
}

interface GoalItem {
  id: string;
  title: string;
  description: string | null;
  status: string;
  progress: number;
  due_date: string | null;
  key_results: KeyResult[];
}

const statusColors: Record<string, string> = {
  on_track: "bg-green-100 text-green-700",
  at_risk: "bg-amber-100 text-amber-700",
  behind: "bg-red-100 text-red-700",
  completed: "bg-blue-100 text-blue-700",
};

export default function GoalsPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showAddKR, setShowAddKR] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [krTitle, setKrTitle] = useState("");
  const [krTarget, setKrTarget] = useState("");
  const [krUnit, setKrUnit] = useState("");

  const { data: goals, isLoading } = useQuery({
    queryKey: ["goals", spaceKey],
    queryFn: async () => {
      const res = await api.get(`/spaces/${spaceKey}/goals`);
      return res.data.data as GoalItem[];
    },
    enabled: !!spaceKey,
  });

  const createGoal = useMutation({
    mutationFn: async () => {
      await api.post(`/spaces/${spaceKey}/goals`, { title: newTitle });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals", spaceKey] });
      setShowCreate(false);
      setNewTitle("");
    },
  });

  const addKR = useMutation({
    mutationFn: async () => {
      await api.post(`/goals/${showAddKR}/key-results`, {
        title: krTitle,
        target_value: parseFloat(krTarget),
        unit: krUnit || undefined,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals", spaceKey] });
      setShowAddKR(null);
      setKrTitle("");
      setKrTarget("");
      setKrUnit("");
    },
  });

  const updateKR = useMutation({
    mutationFn: async ({ id, value }: { id: string; value: number }) => {
      await api.put(`/key-results/${id}`, { current_value: value });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals", spaceKey] });
    },
  });

  return (
    <div className="p-6 max-w-4xl">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Goals & OKRs</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors"
        >
          + New Goal
        </button>
      </header>

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {goals && goals.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
          <p className="text-text-muted">No goals yet. Create one to start tracking OKRs.</p>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {goals?.map((goal) => (
          <div key={goal.id} className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">{goal.title}</h3>
                {goal.description && (
                  <p className="text-xs text-text-muted mt-0.5">{goal.description}</p>
                )}
              </div>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[goal.status]}`}>
                {goal.status.replace("_", " ")}
              </span>
            </div>

            {/* Progress bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-muted">Overall Progress</span>
                <span className="text-xs font-medium text-text-primary">{goal.progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    goal.progress >= 100 ? "bg-status-success" :
                    goal.progress >= 70 ? "bg-brand-blue" :
                    goal.progress >= 40 ? "bg-status-warning" : "bg-status-error"
                  }`}
                  style={{ width: `${Math.min(goal.progress, 100)}%` }}
                />
              </div>
            </div>

            {/* Key Results */}
            <div className="flex flex-col gap-2">
              {goal.key_results.map((kr) => (
                <div key={kr.id} className="flex items-center gap-3 rounded-md bg-surface-tertiary p-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-secondary truncate">{kr.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-brand-sky transition-all"
                          style={{ width: `${Math.min(kr.progress, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-text-muted whitespace-nowrap">
                        {kr.current_value} / {kr.target_value} {kr.unit || ""}
                      </span>
                    </div>
                  </div>
                  <input
                    type="number"
                    defaultValue={kr.current_value}
                    onBlur={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val) && val !== kr.current_value) {
                        updateKR.mutate({ id: kr.id, value: val });
                      }
                    }}
                    className="w-20 rounded border border-slate-200 px-2 py-1 text-xs text-right focus:ring-1 focus:ring-brand-sky outline-none"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={() => setShowAddKR(goal.id)}
              className="mt-2 text-xs text-brand-blue hover:underline"
            >
              + Add Key Result
            </button>
          </div>
        ))}
      </div>

      {/* Create Goal Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Goal">
        <form onSubmit={(e) => { e.preventDefault(); createGoal.mutate(); }}>
          <input type="text" value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Objective title" required autoFocus
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-brand-sky outline-none" />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowCreate(false)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={createGoal.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Create</button>
          </div>
        </form>
      </Modal>

      {/* Add Key Result Modal */}
      <Modal open={!!showAddKR} onClose={() => setShowAddKR(null)} title="Add Key Result">
        <form onSubmit={(e) => { e.preventDefault(); addKR.mutate(); }} className="flex flex-col gap-3">
          <input type="text" value={krTitle} onChange={(e) => setKrTitle(e.target.value)}
            placeholder="Key result (e.g. Increase DAU to 1000)" required autoFocus
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <div className="flex gap-3">
            <input type="number" value={krTarget} onChange={(e) => setKrTarget(e.target.value)}
              placeholder="Target" min="1" step="1" required
              className="w-1/2 rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
            <input type="text" value={krUnit} onChange={(e) => setKrUnit(e.target.value)}
              placeholder="Unit (optional)" maxLength={20}
              className="w-1/2 rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={() => setShowAddKR(null)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={addKR.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Add</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
