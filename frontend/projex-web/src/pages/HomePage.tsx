export default function HomePage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-text-primary mb-2">Welcome to ProjeX Suite</h1>
      <p className="text-text-muted mb-6">Project Management for Indonesian SME Teams</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-text-primary mb-1">Getting Started</h3>
          <p className="text-xs text-text-muted">
            Create a Space to organize your work. Choose Scrum, Kanban, or Bug tracking template.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-text-primary mb-1">API Docs</h3>
          <p className="text-xs text-text-muted">
            Visit <a href="/docs" className="text-brand-blue hover:underline">/docs</a> for the interactive Swagger UI.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-text-primary mb-1">Phase 1</h3>
          <p className="text-xs text-text-muted">
            Auth, Spaces, Work Items, Kanban Board, RBAC — all operational.
          </p>
        </div>
      </div>
    </div>
  );
}
