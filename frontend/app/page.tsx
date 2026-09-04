import { Shield, Terminal, CheckCircle2, Server, Layers } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col justify-between p-8 md:p-16 max-w-5xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border pb-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold shadow-sm">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground">FraudDNA</h1>
            <p className="text-xs text-muted-foreground font-mono">Risk Intelligence & Defense</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Phase 0 Foundation Ready
          </span>
        </div>
      </header>

      {/* Main Hero Card */}
      <section className="my-12 space-y-6">
        <div className="bg-card border border-border rounded-xl p-8 shadow-sm space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight">System Foundation Initialized</h2>
            <p className="text-muted-foreground text-sm leading-relaxed max-w-2xl">
              FraudDNA combines transaction-level ML scoring, relationship-graph analysis, explainable AI,
              grounded RAG, and bounded AI investigation agents with deterministic financial risk policies.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-border">
            <div className="p-4 rounded-lg bg-secondary/50 border border-border/50 space-y-2">
              <div className="flex items-center gap-2 text-foreground font-medium text-sm">
                <Server className="h-4 w-4 text-emerald-600" />
                <span>Backend Core</span>
              </div>
              <p className="text-xs text-muted-foreground">
                FastAPI, Pydantic v2, Python 3.12, Uvicorn, SQLAlchemy
              </p>
              <div className="text-[11px] font-mono text-emerald-700 pt-1">
                GET /api/v1/health ready
              </div>
            </div>

            <div className="p-4 rounded-lg bg-secondary/50 border border-border/50 space-y-2">
              <div className="flex items-center gap-2 text-foreground font-medium text-sm">
                <Layers className="h-4 w-4 text-emerald-600" />
                <span>Database & Graph</span>
              </div>
              <p className="text-xs text-muted-foreground">
                PostgreSQL + pgvector containerized infrastructure
              </p>
              <div className="text-[11px] font-mono text-emerald-700 pt-1">
                docker-compose pgvector:16
              </div>
            </div>

            <div className="p-4 rounded-lg bg-secondary/50 border border-border/50 space-y-2">
              <div className="flex items-center gap-2 text-foreground font-medium text-sm">
                <Terminal className="h-4 w-4 text-emerald-600" />
                <span>Frontend Stack</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Next.js 15, TypeScript, Tailwind CSS, Inter + JetBrains Mono
              </p>
              <div className="text-[11px] font-mono text-emerald-700 pt-1">
                App Router & Strict Types
              </div>
            </div>
          </div>
        </div>

        {/* Foundation Checklist */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground font-mono">
            Foundation Verification
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Modular Monolith Structure</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Strict AI vs Deterministic Policy Boundary</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Ruff, Mypy & Pytest Suites</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Clean Docker Compose Infrastructure</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border pt-6 flex flex-col md:flex-row items-center justify-between text-xs text-muted-foreground gap-2 font-mono">
        <span>FraudDNA MVP — Razorpay Buildathon</span>
        <span>Phase 0 (Foundation) Completed</span>
      </footer>
    </main>
  );
}
