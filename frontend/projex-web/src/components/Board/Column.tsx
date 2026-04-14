import { useDroppable } from "@dnd-kit/core";
import { Card } from "./Card";
import type { BoardColumn } from "@/types/board";

interface ColumnProps {
  column: BoardColumn;
}

export function Column({ column }: ColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${column.status.id}`,
    data: { statusId: column.status.id },
  });

  const isOverLimit =
    column.wip_limit !== undefined && column.count > column.wip_limit;
  const isAtLimit =
    column.wip_limit !== undefined && column.count === column.wip_limit;

  return (
    <div className="flex-shrink-0 w-72 bg-surface-tertiary rounded-lg p-3 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: column.status.color }}
          />
          <h3 className="text-sm font-semibold text-text-primary">
            {column.status.name}
          </h3>
        </div>
        <span
          className={`text-xs rounded-full px-2 py-0.5 ${
            isOverLimit
              ? "bg-red-100 text-red-700"
              : isAtLimit
                ? "bg-amber-100 text-amber-700"
                : "bg-white text-text-muted"
          }`}
        >
          {column.count}
          {column.wip_limit !== undefined && ` / ${column.wip_limit}`}
        </span>
      </div>
      <div
        ref={setNodeRef}
        className={`flex flex-col gap-2 flex-1 min-h-[4rem] rounded-md p-1 transition-colors ${
          isOver ? "bg-brand-sky/10 ring-2 ring-brand-sky/30" : ""
        }`}
      >
        {column.items.map((item) => (
          <Card key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
