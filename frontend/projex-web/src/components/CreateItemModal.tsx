import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Modal } from "./Modal";

interface CreateItemModalProps {
  open: boolean;
  onClose: () => void;
  spaceKey: string;
}

const itemTypes = [
  { value: "epic", label: "Epic" },
  { value: "story", label: "Story" },
  { value: "task", label: "Task" },
  { value: "bug", label: "Bug" },
];

const priorities = [
  { value: "critical", label: "Critical", color: "bg-red-100 text-red-700" },
  { value: "high", label: "High", color: "bg-amber-100 text-amber-700" },
  { value: "normal", label: "Normal", color: "bg-blue-100 text-blue-700" },
  { value: "low", label: "Low", color: "bg-slate-100 text-slate-600" },
];

export function CreateItemModal({ open, onClose, spaceKey }: CreateItemModalProps) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("task");
  const [priority, setPriority] = useState("normal");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/spaces/${spaceKey}/items`, {
        title,
        type,
        priority,
      });
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["board", spaceKey] });
      onClose();
      setTitle("");
      setType("task");
      setPriority("normal");
      setError("");
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to create item";
      setError(msg);
    },
  });

  return (
    <Modal open={open} onClose={onClose} title={`Create Item in ${spaceKey}`}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        {error && (
          <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              placeholder="What needs to be done?"
              required
              autoFocus
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-text-muted mb-1">
                Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              >
                {itemTypes.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1">
              <label className="block text-xs font-medium text-text-muted mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              >
                {priorities.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
