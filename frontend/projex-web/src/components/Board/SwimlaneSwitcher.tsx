import { useBoardStore } from "@/stores/boardStore";

const options = [
  { value: "none" as const, label: "No Swimlanes" },
  { value: "assignee" as const, label: "By Assignee" },
  { value: "priority" as const, label: "By Priority" },
  { value: "epic" as const, label: "By Epic" },
];

export function SwimlaneSwitcher() {
  const swimlaneType = useBoardStore((s) => s.swimlaneType);
  const setSwimlaneType = useBoardStore((s) => s.setSwimlaneType);

  return (
    <select
      value={swimlaneType}
      onChange={(e) =>
        setSwimlaneType(
          e.target.value as "none" | "epic" | "assignee" | "priority",
        )
      }
      className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-text-secondary
                 focus:ring-2 focus:ring-brand-sky focus:ring-offset-1 transition-colors"
      aria-label="Swimlane grouping"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
