import { useDraggable } from "@dnd-kit/core";
import { useBoardStore } from "@/stores/boardStore";
import type { BoardItem } from "@/types/board";

const priorityColors: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-amber-100 text-amber-700",
  normal: "bg-blue-100 text-blue-700",
  low: "bg-slate-100 text-slate-600",
};

const typeIcons: Record<string, string> = {
  epic: "⚡",
  story: "📖",
  task: "✓",
  bug: "🐛",
  sub_task: "↳",
  cr: "🔄",
};

interface CardProps {
  item: BoardItem;
}

export function Card({ item }: CardProps) {
  const selectItem = useBoardStore((s) => s.selectItem);

  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: item.id,
      data: { item },
    });

  const style = transform
    ? {
        transform: `translate(${transform.x}px, ${transform.y}px)`,
        opacity: isDragging ? 0.5 : 1,
        zIndex: isDragging ? 50 : undefined,
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => {
        if (!isDragging) selectItem(item.key);
      }}
      className="rounded-md border border-slate-200 bg-white p-3 shadow-sm cursor-grab active:cursor-grabbing
                 hover:border-brand-sky hover:shadow-md transition-all"
      role="button"
      aria-label={`${item.key}: ${item.title}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-brand-blue">
          {typeIcons[item.type] || "✓"} {item.key}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${priorityColors[item.priority]}`}
        >
          {item.priority}
        </span>
      </div>
      <h4 className="text-sm font-medium text-text-primary line-clamp-2">
        {item.title}
      </h4>
      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-1">
          {item.assignee_id && (
            <div
              className="h-5 w-5 rounded-full bg-brand-blue/20 flex items-center justify-center"
              aria-label="Assigned"
            >
              <span className="text-[10px] text-brand-blue font-medium">
                {item.assignee_id.slice(0, 2).toUpperCase()}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {item.labels.length > 0 && (
            <span className="text-xs text-text-muted">
              {item.labels.length} label{item.labels.length > 1 ? "s" : ""}
            </span>
          )}
          {item.estimate_points !== null && (
            <span className="text-xs text-text-muted">
              {item.estimate_points} SP
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
