export interface BoardStatus {
  id: string;
  name: string;
  category: "todo" | "in_progress" | "done";
  color: string;
  position: number;
}

export interface BoardItem {
  id: string;
  key: string;
  title: string;
  type: "epic" | "story" | "task" | "bug" | "sub_task" | "cr";
  priority: "critical" | "high" | "normal" | "low";
  assignee_id: string | null;
  estimate_points: number | null;
  labels: string[];
  position: number;
}

export interface BoardColumn {
  status: BoardStatus;
  items: BoardItem[];
  count: number;
  wip_limit?: number;
}

export interface QuickFilters {
  assignees: string[];
  types: string[];
  labels: string[];
}

export interface BoardData {
  columns: BoardColumn[];
  swimlanes: { type: string; groups: string[] };
  quick_filters: QuickFilters;
}
