import { useBoardStore } from "@/stores/boardStore";
import type { QuickFilters as QuickFiltersType } from "@/types/board";

interface QuickFiltersProps {
  filters: QuickFiltersType;
}

export function QuickFilters({ filters }: QuickFiltersProps) {
  const activeFilters = useBoardStore((s) => s.activeFilters);
  const setFilter = useBoardStore((s) => s.setFilter);
  const clearFilters = useBoardStore((s) => s.clearFilters);

  const hasActive =
    activeFilters.assignees.length > 0 ||
    activeFilters.types.length > 0 ||
    activeFilters.labels.length > 0;

  const toggleType = (type: string) => {
    const current = activeFilters.types;
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setFilter("types", next);
  };

  const toggleLabel = (label: string) => {
    const current = activeFilters.labels;
    const next = current.includes(label)
      ? current.filter((l) => l !== label)
      : [...current, label];
    setFilter("labels", next);
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-text-muted font-medium">Filter:</span>

      {filters.types.map((type) => (
        <button
          key={type}
          onClick={() => toggleType(type)}
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            activeFilters.types.includes(type)
              ? "bg-brand-blue text-white"
              : "bg-white border border-slate-200 text-text-secondary hover:bg-slate-50"
          }`}
          aria-label={`Filter by type: ${type}`}
        >
          {type}
        </button>
      ))}

      {filters.labels.map((label) => (
        <button
          key={label}
          onClick={() => toggleLabel(label)}
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            activeFilters.labels.includes(label)
              ? "bg-brand-blue text-white"
              : "bg-white border border-slate-200 text-text-secondary hover:bg-slate-50"
          }`}
          aria-label={`Filter by label: ${label}`}
        >
          {label}
        </button>
      ))}

      {hasActive && (
        <button
          onClick={clearFilters}
          className="text-xs text-brand-blue hover:underline"
          aria-label="Clear all filters"
        >
          Clear
        </button>
      )}
    </div>
  );
}
