import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

interface WidgetData {
  id: string;
  widget_type: string;
  title: string;
  size: string;
  data: Record<string, unknown>;
}

interface DashboardData {
  id: string;
  name: string;
  widgets: WidgetData[];
}

const sizeClass: Record<string, string> = {
  small: "col-span-1",
  medium: "col-span-1 md:col-span-2",
  large: "col-span-1 md:col-span-3",
};

const statusColors: Record<string, string> = {
  on_track: "bg-green-100 text-green-700",
  at_risk: "bg-amber-100 text-amber-700",
  behind: "bg-red-100 text-red-700",
  completed: "bg-blue-100 text-blue-700",
};

const priorityColors: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-amber-500",
  normal: "bg-blue-500",
  low: "bg-slate-400",
};

function formatCurrency(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(n);
}

function ItemCountWidget({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <p className="text-4xl font-bold text-brand-blue">{(data.total as number) ?? 0}</p>
        <p className="text-xs text-text-muted mt-1">Total Items</p>
      </div>
    </div>
  );
}

function StatusBreakdownWidget({ data }: { data: Record<string, unknown> }) {
  const statuses = (data.statuses as Array<{ name: string; count: number }>) || [];
  const total = statuses.reduce((s, st) => s + st.count, 0) || 1;
  return (
    <div className="flex flex-col gap-2">
      {statuses.map((st) => (
        <div key={st.name} className="flex items-center gap-2">
          <span className="text-xs text-text-secondary w-24 truncate">{st.name}</span>
          <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full bg-brand-sky" style={{ width: `${(st.count / total) * 100}%` }} />
          </div>
          <span className="text-xs text-text-muted w-8 text-right">{st.count}</span>
        </div>
      ))}
    </div>
  );
}

function PriorityChartWidget({ data }: { data: Record<string, unknown> }) {
  const priorities = (data.priorities as Array<{ name: string; count: number }>) || [];
  const total = priorities.reduce((s, p) => s + p.count, 0) || 1;
  return (
    <div className="flex items-end gap-3 h-full pt-2">
      {priorities.map((p) => (
        <div key={p.name} className="flex flex-col items-center flex-1">
          <span className="text-xs font-medium mb-1">{p.count}</span>
          <div
            className={`w-full rounded-t ${priorityColors[p.name] || "bg-slate-400"}`}
            style={{ height: `${Math.max((p.count / total) * 100, 10)}%`, minHeight: "8px" }}
          />
          <span className="text-[10px] text-text-muted mt-1 capitalize">{p.name}</span>
        </div>
      ))}
    </div>
  );
}

function GoalProgressWidget({ data }: { data: Record<string, unknown> }) {
  const goals = (data.goals as Array<{ title: string; progress: number; status: string }>) || [];
  if (goals.length === 0) return <p className="text-xs text-text-muted">No goals yet</p>;
  return (
    <div className="flex flex-col gap-3">
      {goals.map((g, i) => (
        <div key={i}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-text-secondary truncate flex-1">{g.title}</span>
            <span className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ml-2 ${statusColors[g.status] || ""}`}>
              {g.progress}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full bg-brand-sky transition-all" style={{ width: `${Math.min(g.progress, 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function BudgetSummaryWidget({ data }: { data: Record<string, unknown> }) {
  const total = (data.total as number) || 0;
  const spent = (data.spent as number) || 0;
  const remaining = (data.remaining as number) || 0;
  const pct = total > 0 ? Math.round((spent / total) * 100) : 0;
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2">
      <p className="text-2xl font-bold text-text-primary">{pct}%</p>
      <p className="text-xs text-text-muted">utilized</p>
      <div className="w-full text-center">
        <p className="text-xs text-status-warning">{formatCurrency(spent)} spent</p>
        <p className="text-xs text-status-success">{formatCurrency(remaining)} remaining</p>
      </div>
    </div>
  );
}

const widgetRenderers: Record<string, React.FC<{ data: Record<string, unknown> }>> = {
  item_count: ItemCountWidget,
  status_breakdown: StatusBreakdownWidget,
  priority_chart: PriorityChartWidget,
  goal_progress: GoalProgressWidget,
  budget_summary: BudgetSummaryWidget,
};

export default function DashboardPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard", spaceKey],
    queryFn: async () => {
      const res = await api.get(`/spaces/${spaceKey}/dashboard`);
      return res.data.data as DashboardData;
    },
    enabled: !!spaceKey,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load dashboard
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-text-primary mb-6">{data?.name || "Dashboard"}</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data?.widgets.map((widget) => {
          const Renderer = widgetRenderers[widget.widget_type];
          return (
            <div
              key={widget.id}
              className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${sizeClass[widget.size] || "col-span-1"}`}
            >
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">
                {widget.title}
              </h3>
              <div className="min-h-[100px]">
                {Renderer ? <Renderer data={widget.data} /> : <p className="text-xs text-text-muted">Unknown widget</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
