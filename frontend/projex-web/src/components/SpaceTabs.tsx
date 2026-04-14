import { NavLink, useParams } from "react-router-dom";

export function SpaceTabs() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  if (!spaceKey) return null;

  const tabs = [
    { path: `/spaces/${spaceKey}/board`, label: "Board" },
    { path: `/spaces/${spaceKey}/wiki`, label: "Wiki" },
    { path: `/spaces/${spaceKey}/budget`, label: "Budget" },
    { path: `/spaces/${spaceKey}/goals`, label: "Goals" },
  ];

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-slate-200 px-6">
      <div className="flex items-center gap-1">
        <span className="text-sm font-mono font-bold text-brand-blue mr-4">
          {spaceKey}
        </span>
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              `px-3 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? "border-brand-blue text-brand-blue"
                  : "border-transparent text-text-muted hover:text-text-primary hover:border-slate-300"
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
