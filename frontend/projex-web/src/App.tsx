import { Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";

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
    <Routes>
      <Route
        path="/"
        element={
          <div className="flex h-screen items-center justify-center">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-brand-navy">
                ProjeX Suite
              </h1>
              <p className="mt-2 text-text-muted">
                Project Management for Indonesian SME Teams
              </p>
            </div>
          </div>
        }
      />
      <Route
        path="/spaces/:spaceKey/board"
        element={
          <Suspense fallback={<Spinner />}>
            <BoardPage />
          </Suspense>
        }
      />
    </Routes>
  );
}
