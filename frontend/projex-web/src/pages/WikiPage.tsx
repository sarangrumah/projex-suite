import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";

interface WikiItem {
  id: string;
  parent_id: string | null;
  title: string;
  slug: string;
  position: number;
  updated_at: string;
}

interface WikiDetail {
  id: string;
  title: string;
  slug: string;
  body: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export default function WikiPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const { data: pages, isLoading } = useQuery({
    queryKey: ["wiki", spaceKey],
    queryFn: async () => {
      const res = await api.get(`/spaces/${spaceKey}/wiki`);
      return res.data.data as WikiItem[];
    },
    enabled: !!spaceKey,
  });

  const { data: detail } = useQuery({
    queryKey: ["wiki-page", selectedId],
    queryFn: async () => {
      const res = await api.get(`/wiki/${selectedId}`);
      return res.data.data as WikiDetail;
    },
    enabled: !!selectedId,
  });

  const createMutation = useMutation({
    mutationFn: async (title: string) => {
      const res = await api.post(`/spaces/${spaceKey}/wiki`, {
        title,
        body: { type: "doc", content: [{ type: "paragraph", text: "" }] },
      });
      return res.data.data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["wiki", spaceKey] });
      setSelectedId(data.id);
      setShowCreate(false);
      setNewTitle("");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      let bodyJson: Record<string, unknown>;
      try {
        bodyJson = JSON.parse(editBody);
      } catch {
        bodyJson = {
          type: "doc",
          content: [{ type: "paragraph", text: editBody }],
        };
      }
      const res = await api.put(`/wiki/${selectedId}`, {
        title: editTitle,
        body: bodyJson,
      });
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wiki", spaceKey] });
      qc.invalidateQueries({ queryKey: ["wiki-page", selectedId] });
      setEditing(false);
    },
  });

  const startEdit = () => {
    if (detail) {
      setEditTitle(detail.title);
      setEditBody(JSON.stringify(detail.body, null, 2));
      setEditing(true);
    }
  };

  const bodyText = (body: Record<string, unknown>): string => {
    if (!body) return "";
    const content = body.content as Array<{ text?: string; content?: Array<{ text?: string }> }> | undefined;
    if (!content) return JSON.stringify(body);
    return content
      .map((block) => block.text || (block.content?.map((c) => c.text || "").join("")) || "")
      .join("\n");
  };

  return (
    <div className="flex h-full">
      {/* Sidebar — page list */}
      <div className="w-64 border-r border-slate-200 bg-white flex flex-col flex-shrink-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-text-primary">Wiki</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="text-xs text-brand-blue hover:underline"
          >
            + New
          </button>
        </div>

        {showCreate && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (newTitle.trim()) createMutation.mutate(newTitle.trim());
            }}
            className="px-3 py-2 border-b border-slate-100"
          >
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Page title..."
              className="w-full rounded border border-slate-200 px-2 py-1 text-xs focus:ring-1 focus:ring-brand-sky outline-none"
              autoFocus
            />
            <div className="flex gap-1 mt-1">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="text-xs text-white bg-brand-blue rounded px-2 py-0.5"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="text-xs text-text-muted"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className="flex-1 overflow-y-auto py-1">
          {isLoading && (
            <p className="px-4 py-2 text-xs text-text-muted">Loading...</p>
          )}
          {pages?.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                setSelectedId(p.id);
                setEditing(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                selectedId === p.id
                  ? "bg-brand-50 text-brand-blue font-medium"
                  : "text-text-secondary hover:bg-slate-50"
              }`}
            >
              {p.title}
            </button>
          ))}
          {pages && pages.length === 0 && (
            <p className="px-4 py-4 text-xs text-text-muted text-center">
              No pages yet
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {!selectedId && (
          <div className="flex items-center justify-center h-full text-text-muted text-sm">
            Select a page or create a new one
          </div>
        )}

        {selectedId && detail && !editing && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold text-text-primary">
                {detail.title}
              </h1>
              <button
                onClick={startEdit}
                className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-slate-50 transition-colors"
              >
                Edit
              </button>
            </div>
            <div className="prose prose-sm max-w-none text-text-secondary whitespace-pre-wrap">
              {bodyText(detail.body)}
            </div>
            <div className="mt-6 text-xs text-text-muted">
              Last updated: {new Date(detail.updated_at).toLocaleString()}
            </div>
          </div>
        )}

        {selectedId && editing && (
          <div className="flex flex-col gap-4">
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="text-2xl font-bold text-text-primary border-b border-slate-200 pb-2 outline-none focus:border-brand-sky"
            />
            <textarea
              value={editBody}
              onChange={(e) => setEditBody(e.target.value)}
              rows={20}
              className="w-full rounded-md border border-slate-200 p-3 text-sm font-mono text-text-secondary focus:ring-2 focus:ring-brand-sky outline-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
                className="rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors disabled:opacity-50"
              >
                {updateMutation.isPending ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
