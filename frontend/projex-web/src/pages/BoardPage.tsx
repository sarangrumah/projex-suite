import { useParams } from "react-router-dom";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import { useState } from "react";
import { useBoard, useMoveItem } from "@/hooks/useBoard";
import { useBoardStore } from "@/stores/boardStore";
import { Column } from "@/components/Board/Column";
import { Card } from "@/components/Board/Card";
import { QuickFilters } from "@/components/Board/QuickFilters";
import { CreateItemModal } from "@/components/CreateItemModal";
import { SwimlaneSwitcher } from "@/components/Board/SwimlaneSwitcher";
import { DetailPanel } from "@/components/ItemDetail/DetailPanel";
import type { BoardItem } from "@/types/board";

export default function BoardPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const { data, isLoading, error } = useBoard(spaceKey!);
  const moveItemMutation = useMoveItem(spaceKey!);
  const columns = useBoardStore((s) => s.columns);
  const activeFilters = useBoardStore((s) => s.activeFilters);
  const selectedItemKey = useBoardStore((s) => s.selectedItemKey);

  const [activeItem, setActiveItem] = useState<BoardItem | null>(null);
  const [showCreateItem, setShowCreateItem] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  const handleDragStart = (event: { active: { data: { current?: { item?: BoardItem } } } }) => {
    const item = event.active.data.current?.item;
    if (item) setActiveItem(item);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveItem(null);
    const { active, over } = event;
    if (!over) return;

    const item = active.data.current?.item as BoardItem | undefined;
    if (!item) return;

    // The droppable column sets data.statusId
    const targetStatusId = over.data.current?.statusId as string | undefined;
    if (!targetStatusId) return;

    // Find which column the item is currently in
    const currentCol = columns.find((c) =>
      c.items.some((i) => i.id === item.id),
    );
    // Skip if dropping in the same column
    if (currentCol && currentCol.status.id === targetStatusId) return;

    moveItemMutation.mutate({
      itemKey: item.key,
      itemId: item.id,
      statusId: targetStatusId,
      position: 0,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load board: {error.message}
        </div>
      </div>
    );
  }

  // Apply filters
  const filteredColumns = columns.map((col) => ({
    ...col,
    items: col.items.filter((item) => {
      if (
        activeFilters.types.length > 0 &&
        !activeFilters.types.includes(item.type)
      )
        return false;
      if (
        activeFilters.labels.length > 0 &&
        !item.labels.some((l) => activeFilters.labels.includes(l))
      )
        return false;
      if (
        activeFilters.assignees.length > 0 &&
        (!item.assignee_id ||
          !activeFilters.assignees.includes(item.assignee_id))
      )
        return false;
      return true;
    }),
    count: col.items.length, // Keep original count
  }));

  return (
    <div className="flex flex-col gap-4 p-6 h-full">
      {/* Header */}
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">
          {spaceKey} Board
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateItem(true)}
            className="inline-flex items-center gap-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors"
          >
            + Create Item
          </button>
          <SwimlaneSwitcher />
        </div>
      </header>

      <CreateItemModal
        open={showCreateItem}
        onClose={() => setShowCreateItem(false)}
        spaceKey={spaceKey!}
      />

      {/* Quick filters */}
      {data?.quick_filters && <QuickFilters filters={data.quick_filters} />}

      {/* Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 flex-1 min-h-[calc(100vh-12rem)]">
          {filteredColumns.map((column) => (
            <Column key={column.status.id} column={column} />
          ))}
        </div>

        <DragOverlay>
          {activeItem ? (
            <div className="w-72 rotate-2 opacity-90">
              <Card item={activeItem} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Item detail slide-in panel */}
      {selectedItemKey && <DetailPanel />}
    </div>
  );
}
