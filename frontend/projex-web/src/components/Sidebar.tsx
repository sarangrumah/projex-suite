import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

const navItems = [
  { path: "/", label: "Home", icon: "H" },
  { path: "/spaces", label: "Spaces", icon: "S" },
];

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="flex flex-col w-60 bg-brand-navy text-white h-screen flex-shrink-0">
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
        {user ? (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center text-xs font-bold">
              {user.display_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">{user.display_name}</p>
              <p className="text-xs text-slate-400 truncate">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-slate-400 hover:text-white transition-colors"
              aria-label="Logout"
            >
              Exit
            </button>
          </div>
        ) : (
          <NavLink
            to="/login"
            className="flex items-center justify-center gap-2 px-4 py-2 text-sm rounded-md bg-brand-blue hover:bg-brand-blue/90 transition-colors"
          >
            Sign In
          </NavLink>
        )}
      </div>
    </nav>
  );
}
