import { Routes, Route, useLocation } from "react-router-dom";
import { lazy, Suspense, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuthStore } from "@/stores/authStore";

const HomePage = lazy(() => import("@/pages/HomePage"));
const SpacesPage = lazy(() => import("@/pages/SpacesPage"));
const BoardPage = lazy(() => import("@/pages/BoardPage"));
const WikiPage = lazy(() => import("@/pages/WikiPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/pages/RegisterPage"));

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
    </div>
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

  // Auth pages render without sidebar
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
      <main className="flex-1 overflow-y-auto">
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
            <Route
              path="/spaces/:spaceKey/board"
              element={
                <ProtectedRoute>
                  <BoardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/spaces/:spaceKey/wiki"
              element={
                <ProtectedRoute>
                  <WikiPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
