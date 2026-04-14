import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/services/api";

interface SpaceItem {
  id: string;
  name: string;
  key: string;
  description: string | null;
  template: string;
  status: string;
  created_at: string;
}

export default function SpacesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["spaces"],
    queryFn: async () => {
      const res = await api.get("/spaces/");
      return res.data as { data: SpaceItem[]; meta: { total: number } };
    },
  });

  return (
    <div className="p-6">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Spaces</h1>
      </header>

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
          Login required to view spaces. Use the API at <a href="/docs" className="underline">/docs</a> to register and login first.
        </div>
      )}

      {data && data.data.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
          <p className="text-text-muted mb-2">No spaces yet</p>
          <p className="text-xs text-text-muted">
            Create one via POST /api/v1/spaces/ in <a href="/docs" className="text-brand-blue hover:underline">Swagger UI</a>
          </p>
        </div>
      )}

      {data && data.data.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.data.map((space) => (
            <Link
              key={space.id}
              to={`/spaces/${space.key}/board`}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md hover:border-brand-sky transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="w-8 h-8 rounded bg-brand-blue/10 flex items-center justify-center text-xs font-mono font-bold text-brand-blue">
                  {space.key}
                </span>
                <h3 className="text-sm font-semibold text-text-primary">{space.name}</h3>
              </div>
              {space.description && (
                <p className="text-xs text-text-muted line-clamp-2 mb-2">{space.description}</p>
              )}
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-blue">
                  {space.template}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-text-muted">
                  <span className="h-1.5 w-1.5 rounded-full bg-status-success" />
                  {space.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
