import { NavLink } from "react-router-dom";

const navItems = [
  { path: "/", label: "Home", icon: "H" },
  { path: "/spaces", label: "Spaces", icon: "S" },
];

export function Sidebar() {
  return (
    <nav className="flex flex-col w-60 bg-brand-navy text-white h-screen">
      <div className="p-4 border-b border-white/10">
        <span className="text-lg font-bold text-brand-sky">ProjeX</span>
        <span className="text-xs text-slate-400 ml-1">Suite</span>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2 text-sm rounded-md mx-2 transition-colors ${
                isActive
                  ? "bg-white/10 text-white"
                  : "text-slate-300 hover:bg-white/10 hover:text-white"
              }`
            }
            aria-label={item.label}
          >
            <span className="w-5 h-5 rounded bg-white/10 flex items-center justify-center text-xs font-mono">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </div>
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center text-xs font-bold">
            A
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white truncate">Admin</p>
            <p className="text-xs text-slate-400 truncate">demo tenant</p>
          </div>
        </div>
      </div>
    </nav>
  );
}
