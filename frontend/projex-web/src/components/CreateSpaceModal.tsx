import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Modal } from "./Modal";

interface CreateSpaceModalProps {
  open: boolean;
  onClose: () => void;
}

const templates = [
  { value: "scrum", label: "Scrum", desc: "Sprints, backlog, story points" },
  { value: "kanban", label: "Kanban", desc: "Continuous flow, WIP limits" },
  { value: "bug", label: "Bug Tracking", desc: "Issue lifecycle management" },
  { value: "blank", label: "Blank", desc: "Start from scratch" },
];

export function CreateSpaceModal({ open, onClose }: CreateSpaceModalProps) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [template, setTemplate] = useState("scrum");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await api.post("/spaces/", {
        name,
        key: key || undefined,
        template,
      });
      return res.data.data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["spaces"] });
      onClose();
      setName("");
      setKey("");
      setTemplate("scrum");
      setError("");
      navigate(`/spaces/${data.key}/board`);
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to create space";
      setError(msg);
    },
  });

  const handleNameChange = (val: string) => {
    setName(val);
    if (!key) {
      // Auto-suggest key from name
      const words = val.toUpperCase().split(/\s+/).filter(Boolean);
      const suggested =
        words.length === 1
          ? words[0].replace(/[^A-Z0-9]/g, "").slice(0, 5)
          : words.map((w) => w[0]).join("").slice(0, 5);
      setKey(suggested || "");
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Space">
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
              Space Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              placeholder="e.g. Drone Project"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">
              Key (2-10 uppercase chars)
            </label>
            <input
              type="text"
              value={key}
              onChange={(e) => setKey(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10))}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              placeholder="AUTO"
              maxLength={10}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-2">
              Template
            </label>
            <div className="grid grid-cols-2 gap-2">
              {templates.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setTemplate(t.value)}
                  className={`rounded-md border p-3 text-left transition-colors ${
                    template === t.value
                      ? "border-brand-blue bg-brand-50 ring-1 ring-brand-blue"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span className="block text-sm font-medium text-text-primary">
                    {t.label}
                  </span>
                  <span className="block text-xs text-text-muted mt-0.5">
                    {t.desc}
                  </span>
                </button>
              ))}
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
              {mutation.isPending ? "Creating..." : "Create Space"}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
