import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useBoardStore } from "@/stores/boardStore";
import type { BoardData } from "@/types/board";

export function useBoard(spaceKey: string) {
  const setColumns = useBoardStore((s) => s.setColumns);

  return useQuery({
    queryKey: ["board", spaceKey],
    queryFn: async (): Promise<BoardData> => {
      const res = await api.get(`/spaces/${spaceKey}/board`);
      const data = res.data.data as BoardData;
      setColumns(data.columns);
      return data;
    },
    enabled: !!spaceKey,
  });
}

export function useMoveItem(spaceKey: string) {
  const qc = useQueryClient();
  const moveItem = useBoardStore((s) => s.moveItem);

  return useMutation({
    mutationFn: async (vars: {
      itemKey: string;
      itemId: string;
      statusId: string;
      position: number;
    }) => {
      const res = await api.put(`/items/${vars.itemKey}/move`, {
        status_id: vars.statusId,
        position: vars.position,
      });
      return res.data.data;
    },
    onMutate: (vars) => {
      // Optimistic update
      moveItem(vars.itemId, vars.statusId, vars.position);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["board", spaceKey] });
    },
  });
}

export function useWorkflow(spaceKey: string) {
  return useQuery({
    queryKey: ["workflow", spaceKey],
    queryFn: async () => {
      const res = await api.get(`/spaces/${spaceKey}/workflow`);
      return res.data.data;
    },
    enabled: !!spaceKey,
  });
}
