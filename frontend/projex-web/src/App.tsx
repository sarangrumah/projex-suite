import { Routes, Route, useLocation, Outlet } from "react-router-dom";
import { lazy, Suspense, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { SpaceTabs } from "@/components/SpaceTabs";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuthStore } from "@/stores/authStore";
import { EraChatWidget } from "@/components/EraChatWidget";

const HomePage = lazy(() => import("@/pages/HomePage"));
const SpacesPage = lazy(() => import("@/pages/SpacesPage"));
const BoardPage = lazy(() => import("@/pages/BoardPage"));
const WikiPage = lazy(() => import("@/pages/WikiPage"));
const BudgetPage = lazy(() => import("@/pages/BudgetPage"));
const GoalsPage = lazy(() => import("@/pages/GoalsPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const SprintsPage = lazy(() => import("@/pages/SprintsPage"));
const UsersPage = lazy(() => import("@/pages/UsersPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/pages/RegisterPage"));

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function SpaceLayout() {
  return (
    <ProtectedRoute>
      <SpaceTabs />
      <Outlet />
    </ProtectedRoute>
  );
}

const authPages = ["/login", "/register"];

export function App() {
  const location = useLocation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const isAuthPage = authPages.includes(location.pathname);

  useEffect(() => {
    if (isAuthenticated) {
      fetchMe();
    }
  }, [isAuthenticated, fetchMe]);

  if (isAuthPage) {
    return (
      <Suspense fallback={<Spinner />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </Suspense>
    );
  }

  return (
    <div className="flex h-screen bg-surface-secondary">
      <Sidebar />
      <main className="flex-1 overflow-y-auto flex flex-col">
        <Suspense fallback={<Spinner />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route
              path="/spaces"
              element={
                <ProtectedRoute>
                  <SpacesPage />
                </ProtectedRoute>
              }
            />
            <Route path="/spaces/:spaceKey" element={<SpaceLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="board" element={<BoardPage />} />
              <Route path="wiki" element={<WikiPage />} />
              <Route path="budget" element={<BudgetPage />} />
              <Route path="goals" element={<GoalsPage />} />
              <Route path="sprints" element={<SprintsPage />} />
            </Route>
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Suspense>
      </main>
      <EraChatWidget />
    </div>
  );
}
