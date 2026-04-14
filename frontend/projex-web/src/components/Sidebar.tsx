import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/authStore";
import { api } from "@/services/api";

const navItems = [
  { path: "/", label: "Home", icon: "H" },
  { path: "/spaces", label: "Spaces", icon: "S" },
  { path: "/admin/users", label: "Users", icon: "U", adminOnly: true },
];

interface NotifItem {
  id: string;
  type: string;
  title: string;
  body: string | null;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showNotifs, setShowNotifs] = useState(false);

  const { data: notifData } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await api.get("/notifications/");
      return res.data as { data: NotifItem[]; meta: { unread_count: number } };
    },
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });

  const markAllRead = useMutation({
    mutationFn: () => api.put("/notifications/read-all"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unreadCount = notifData?.meta?.unread_count ?? 0;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const visibleNav = navItems.filter(
    (item) => !item.adminOnly || user?.role === "admin",
  );

  return (
    <nav className="flex flex-col w-60 bg-brand-navy text-white h-screen flex-shrink-0">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <span className="text-lg font-bold text-brand-sky">ProjeX</span>
          <span className="text-xs text-slate-400 ml-1">Suite</span>
        </div>
        {isAuthenticated && (
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative p-1.5 rounded hover:bg-white/10 transition-colors"
            aria-label="Notifications"
          >
            <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-status-error text-[10px] font-bold flex items-center justify-center">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>
        )}
      </div>

      {/* Notification dropdown */}
      {showNotifs && (
        <div className="border-b border-white/10 max-h-64 overflow-y-auto">
          <div className="flex items-center justify-between px-4 py-2">
            <span className="text-xs text-slate-400 font-medium">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead.mutate()}
                className="text-[10px] text-brand-sky hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          {notifData?.data.length === 0 && (
            <p className="px-4 py-3 text-xs text-slate-500 text-center">No notifications</p>
          )}
          {notifData?.data.slice(0, 10).map((n) => (
            <div
              key={n.id}
              className={`px-4 py-2 text-xs border-t border-white/5 ${n.is_read ? "opacity-50" : ""}`}
            >
              <p className="text-slate-200 truncate">{n.title}</p>
              {n.body && <p className="text-slate-400 truncate">{n.body}</p>}
            </div>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-2">
        {visibleNav.map((item) => (
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
