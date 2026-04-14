import { Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import { Sidebar } from "@/components/Sidebar";

const HomePage = lazy(() => import("@/pages/HomePage"));
const SpacesPage = lazy(() => import("@/pages/SpacesPage"));
const BoardPage = lazy(() => import("@/pages/BoardPage"));

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="h-8 w-8 border-4 border-brand-sky border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function App() {
  return (
    <div className="flex h-screen bg-surface-secondary">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Suspense fallback={<Spinner />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/spaces" element={<SpacesPage />} />
            <Route path="/spaces/:spaceKey/board" element={<BoardPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
