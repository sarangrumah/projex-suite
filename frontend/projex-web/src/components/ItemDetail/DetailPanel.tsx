import { useBoardStore } from "@/stores/boardStore";

export function DetailPanel() {
  const selectedItemKey = useBoardStore((s) => s.selectedItemKey);
  const selectItem = useBoardStore((s) => s.selectItem);
  const columns = useBoardStore((s) => s.columns);

  if (!selectedItemKey) return null;

  // Find the item across all columns
  let selectedItem = null;
  for (const col of columns) {
    const found = col.items.find((i) => i.key === selectedItemKey);
    if (found) {
      selectedItem = found;
      break;
    }
  }

  if (!selectedItem) return null;

  const priorityColors: Record<string, string> = {
    critical: "bg-red-100 text-red-700",
    high: "bg-amber-100 text-amber-700",
    normal: "bg-blue-100 text-blue-700",
    low: "bg-slate-100 text-slate-600",
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l border-slate-200 shadow-lg z-20 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
        <span className="text-sm font-mono text-brand-blue font-semibold">
          {selectedItem.key}
        </span>
        <button
          onClick={() => selectItem(null)}
          className="rounded-md p-1 hover:bg-slate-100 transition-colors"
          aria-label="Close detail panel"
        >
          <svg
            className="h-5 w-5 text-text-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          {selectedItem.title}
        </h2>

        <div className="flex flex-col gap-4">
          {/* Type */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-text-muted">Type</span>
            <span className="text-sm text-text-secondary capitalize">
              {selectedItem.type.replace("_", " ")}
            </span>
          </div>

          {/* Priority */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-text-muted">Priority</span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${priorityColors[selectedItem.priority]}`}
            >
              {selectedItem.priority}
            </span>
          </div>

          {/* Story Points */}
          {selectedItem.estimate_points !== null && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">Story Points</span>
              <span className="text-sm text-text-secondary">
                {selectedItem.estimate_points}
              </span>
            </div>
          )}

          {/* Labels */}
          {selectedItem.labels.length > 0 && (
            <div>
              <span className="text-xs text-text-muted block mb-1">Labels</span>
              <div className="flex flex-wrap gap-1">
                {selectedItem.labels.map((label) => (
                  <span
                    key={label}
                    className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-blue"
                  >
                    {label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Placeholder sections */}
        <div className="mt-6 border-t border-slate-100 pt-4">
          <h3 className="text-sm font-semibold text-text-primary mb-2">
            Description
          </h3>
          <p className="text-sm text-text-muted italic">No description yet</p>
        </div>

        <div className="mt-6 border-t border-slate-100 pt-4">
          <h3 className="text-sm font-semibold text-text-primary mb-2">
            Comments
          </h3>
          <p className="text-sm text-text-muted italic">No comments yet</p>
        </div>
      </div>
    </div>
  );
}
