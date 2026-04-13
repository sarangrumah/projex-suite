import { create } from "zustand";
import type { BoardColumn, BoardItem } from "@/types/board";

interface BoardState {
  columns: BoardColumn[];
  activeFilters: {
    assignees: string[];
    types: string[];
    labels: string[];
  };
  swimlaneType: "none" | "epic" | "assignee" | "priority";
  selectedItemKey: string | null;

  setColumns: (columns: BoardColumn[]) => void;
  moveItem: (itemId: string, toStatusId: string, toPosition: number) => void;
  setFilter: (key: "assignees" | "types" | "labels", values: string[]) => void;
  clearFilters: () => void;
  setSwimlaneType: (type: "none" | "epic" | "assignee" | "priority") => void;
  selectItem: (key: string | null) => void;
}

export const useBoardStore = create<BoardState>((set) => ({
  columns: [],
  activeFilters: { assignees: [], types: [], labels: [] },
  swimlaneType: "none",
  selectedItemKey: null,

  setColumns: (columns) => set({ columns }),

  moveItem: (itemId, toStatusId, toPosition) =>
    set((state) => {
      const newColumns = state.columns.map((col) => ({
        ...col,
        items: col.items.filter((i) => i.id !== itemId),
        count: col.items.filter((i) => i.id !== itemId).length,
      }));

      // Find the item from any column
      let movedItem: BoardItem | undefined;
      for (const col of state.columns) {
        movedItem = col.items.find((i) => i.id === itemId);
        if (movedItem) break;
      }
      if (!movedItem) return state;

      const targetCol = newColumns.find((c) => c.status.id === toStatusId);
      if (!targetCol) return state;

      const updatedItem = { ...movedItem, position: toPosition };
      targetCol.items.splice(toPosition, 0, updatedItem);
      targetCol.count = targetCol.items.length;

      return { columns: newColumns };
    }),

  setFilter: (key, values) =>
    set((state) => ({
      activeFilters: { ...state.activeFilters, [key]: values },
    })),

  clearFilters: () =>
    set({ activeFilters: { assignees: [], types: [], labels: [] } }),

  setSwimlaneType: (type) => set({ swimlaneType: type }),

  selectItem: (key) => set({ selectedItemKey: key }),
}));
