import { Routes, Route } from "react-router-dom";

export function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <div className="flex h-screen items-center justify-center">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-brand-navy">ProjeX Suite</h1>
              <p className="mt-2 text-text-muted">Project Management for Indonesian SME Teams</p>
            </div>
          </div>
        }
      />
    </Routes>
  );
}
