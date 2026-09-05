"use client";

import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Scale } from "lucide-react";

// ─── PageHeader ──────────────────────────────────────────────
export function PageHeader({
  eyebrow,
  title,
  description,
  badge,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  badge?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[#1C1D22]">
      <div>
        {eyebrow && (
          <p className="text-[11px] font-mono tracking-widest text-[#9194A1] uppercase mb-1.5 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
            {eyebrow}
          </p>
        )}
        <h1 className="font-serif text-2xl md:text-3xl lg:text-4xl text-[#FFFFFF] tracking-tight font-normal">
          {title}
        </h1>
        {description && (
          <p className="text-xs md:text-sm text-[#9194A1] mt-1.5 max-w-2xl font-sans leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {(badge || action) && (
        <div className="flex items-center gap-2.5 shrink-0">
          {badge}
          {action}
        </div>
      )}
    </div>
  );
}

// ─── MetricCard ──────────────────────────────────────────────
export function MetricCard({
  label,
  value,
  sublabel,
  trend,
  icon,
  variant = "default",
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: string;
  icon?: ReactNode;
  variant?:
    | "default"
    | "low"
    | "review"
    | "high"
    | "critical"
    | "copper"
    | "gilded"
    | "success"
    | "warning"
    | "danger";
}) {
  // Normalize alias variants
  const normalizedVariant =
    variant === "success"
      ? "low"
      : variant === "warning"
      ? "review"
      : variant === "danger"
      ? "critical"
      : variant;

  const accentBorder: Record<string, string> = {
    default: "border-[#1C1D22] hover:border-[#2E3038]",
    low: "border-[#1C1D22] hover:border-[#8FAF9B]/40",
    review: "border-[#1C1D22] hover:border-[#C7A66B]/40",
    high: "border-[#1C1D22] hover:border-[#C47A63]/40",
    critical: "border-[#1C1D22] hover:border-[#D05B5B]/40",
    copper: "border-[#1C1D22] hover:border-[#CC9166]/40",
    gilded: "border-[#AE9357]/40 hover:border-[#AE9357]",
  };

  const valueColors: Record<string, string> = {
    default: "text-[#FFFFFF]",
    low: "text-[#8FAF9B]",
    review: "text-[#C7A66B]",
    high: "text-[#C47A63]",
    critical: "text-[#D05B5B]",
    copper: "text-[#CC9166]",
    gilded: "text-[#AE9357]",
  };

  return (
    <div
      className={`bg-[#040406] rounded-[10px] border p-5 transition-all duration-200 ${
        accentBorder[normalizedVariant] || accentBorder.default
      }`}
    >
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-[11px] font-mono uppercase tracking-wider text-[#9194A1]">
          {label}
        </span>
        {icon && <span className="text-[#777A88]">{icon}</span>}
      </div>
      <p
        className={`font-serif text-2xl md:text-3xl font-medium tracking-tight ${
          valueColors[normalizedVariant] || valueColors.default
        }`}
      >
        {value}
      </p>
      {sublabel && (
        <p className="text-xs text-[#777A88] mt-1.5 font-sans truncate">{sublabel}</p>
      )}
      {trend && (
        <p className="text-[11px] font-mono text-[#9194A1] mt-1 flex items-center gap-1">
          <span className="text-[#CC9166]">↗</span> {trend}
        </p>
      )}
    </div>
  );
}

// ─── RiskBadge ───────────────────────────────────────────────
export function RiskBadge({
  level,
  size = "sm",
}: {
  level: string;
  size?: "xs" | "sm" | "md";
}) {
  const k = level.toLowerCase();

  const styles: Record<string, string> = {
    low: "bg-[#8FAF9B]/10 text-[#8FAF9B] border-[#8FAF9B]/30",
    allow: "bg-[#8FAF9B]/10 text-[#8FAF9B] border-[#8FAF9B]/30",
    medium: "bg-[#C7A66B]/10 text-[#C7A66B] border-[#C7A66B]/30",
    review: "bg-[#C7A66B]/10 text-[#C7A66B] border-[#C7A66B]/30",
    high: "bg-[#C47A63]/10 text-[#C47A63] border-[#C47A63]/30",
    critical: "bg-[#D05B5B]/10 text-[#D05B5B] border-[#D05B5B]/30",
    hold: "bg-[#D05B5B]/10 text-[#D05B5B] border-[#D05B5B]/30",
    info: "bg-[#A6A9B3]/10 text-[#A6A9B3] border-[#A6A9B3]/30",
  };

  const sizes: Record<string, string> = {
    xs: "text-[10px] px-2 py-0.5",
    sm: "text-[11px] px-2.5 py-0.5",
    md: "text-xs px-3 py-1",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono uppercase tracking-wider font-medium ${
        styles[k] || styles.info
      } ${sizes[size]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
      {level.toUpperCase()}
    </span>
  );
}

// ─── DecisionBadge ───────────────────────────────────────────
export function DecisionBadge({
  action,
  size = "md",
}: {
  action: string;
  size?: "xs" | "sm" | "md" | "lg";
}) {
  const act = action.toUpperCase();

  const styles: Record<string, { bg: string; text: string; border: string }> = {
    ALLOW: {
      bg: "bg-[#8FAF9B]/15",
      text: "text-[#8FAF9B]",
      border: "border-[#8FAF9B]/40",
    },
    REVIEW: {
      bg: "bg-[#C7A66B]/15",
      text: "text-[#C7A66B]",
      border: "border-[#C7A66B]/40",
    },
    HOLD: {
      bg: "bg-[#D05B5B]/15",
      text: "text-[#D05B5B]",
      border: "border-[#D05B5B]/40",
    },
  };

  const sizes: Record<string, string> = {
    xs: "text-[10px] px-2 py-0.5",
    sm: "text-[11px] px-2.5 py-1",
    md: "text-xs px-3.5 py-1.5",
    lg: "text-sm px-5 py-2 font-semibold",
  };

  const current = styles[act] || {
    bg: "bg-[#1C1D22]",
    text: "text-[#E2E3E9]",
    border: "border-[#2E3038]",
  };

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border font-mono tracking-wider font-bold ${current.bg} ${current.text} ${current.border} ${sizes[size]}`}
    >
      <span className="h-2 w-2 rounded-full bg-current" />
      {act}
    </span>
  );
}

// ─── StatusPill ──────────────────────────────────────────────
export function StatusPill({
  label,
  status = "neutral",
}: {
  label: string;
  status?: "active" | "warning" | "danger" | "copper" | "neutral";
}) {
  const dotColors: Record<string, string> = {
    active: "bg-[#8FAF9B]",
    warning: "bg-[#C7A66B]",
    danger: "bg-[#D05B5B]",
    copper: "bg-[#CC9166]",
    neutral: "bg-[#777A88]",
  };

  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono text-[#9194A1] bg-[#121317] border border-[#1C1D22]">
      <span className={`h-1.5 w-1.5 rounded-full ${dotColors[status]}`} />
      {label}
    </span>
  );
}

// ─── SectionCard ─────────────────────────────────────────────
export function SectionCard({
  title,
  subtitle,
  children,
  action,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-[#040406] rounded-[10px] border border-[#1C1D22] overflow-hidden ${className}`}>
      <div className="px-5 py-3.5 border-b border-[#1C1D22] flex items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-mono uppercase tracking-wider text-[#FFFFFF] font-medium">
            {title}
          </h3>
          {subtitle && (
            <p className="text-[11px] text-[#777A88] mt-0.5 font-sans">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

// ─── DataLabel ───────────────────────────────────────────────
export function DataLabel({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-mono text-[#9194A1] bg-[#121317] border border-[#1C1D22]">
      {label}
    </span>
  );
}

// ─── ShapBars ────────────────────────────────────────────────
export function ShapBars({
  factors,
}: {
  factors: Array<{
    feature: string;
    impact: number;
    direction: string;
    value?: unknown;
    rank?: number;
  }>;
}) {
  if (!factors || factors.length === 0) {
    return (
      <p className="text-xs text-[#777A88] font-sans italic py-2">
        No local risk attribution factors recorded.
      </p>
    );
  }

  const maxImpact = Math.max(...factors.map((f) => Math.abs(f.impact)), 0.001);

  return (
    <div className="space-y-3">
      {factors.slice(0, 6).map((factor, idx) => {
        const isRisk =
          factor.direction === "increases_risk" ||
          factor.impact > 0 ||
          factor.direction === "high";
        const widthPct = Math.min(100, (Math.abs(factor.impact) / maxImpact) * 100);

        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-mono text-[#E2E3E9] truncate max-w-[180px]">
                {factor.feature}
              </span>
              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                <span className={isRisk ? "text-[#C47A63]" : "text-[#8FAF9B]"}>
                  {isRisk ? "Elevates Risk" : "Mitigates"}
                </span>
                <span
                  className={`px-1.5 py-0.2 rounded font-semibold ${
                    isRisk
                      ? "bg-[#C47A63]/10 text-[#C47A63] border border-[#C47A63]/30"
                      : "bg-[#8FAF9B]/10 text-[#8FAF9B] border border-[#8FAF9B]/30"
                  }`}
                >
                  {isRisk ? "+" : "-"}
                  {Math.abs(factor.impact).toFixed(3)}
                </span>
              </div>
            </div>
            <div className="h-1.5 w-full bg-[#121317] rounded-full overflow-hidden flex border border-[#1C1D22]">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isRisk ? "bg-[#C47A63]" : "bg-[#8FAF9B]"
                }`}
                style={{ width: `${Math.max(8, widthPct)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── InvestigationTimeline ───────────────────────────────────
export function InvestigationTimeline({
  steps,
  currentStep = 6,
  toolTrace,
}: {
  steps?:
    | number
    | Array<{
        step: string;
        title: string;
        status: "completed" | "active" | "pending";
        detail?: string;
        duration?: string;
      }>;
  currentStep?: number;
  toolTrace?: Array<{
    tool_name: string;
    status: string;
    duration_ms: number;
    error_message?: string | null;
  }>;
}) {
  type StepItem = {
    step: string;
    title: string;
    status: "completed" | "active" | "pending";
    detail?: string;
    duration?: string;
  };

  const defaultSteps: StepItem[] = [
    {
      step: "01",
      title: "Transaction context loaded",
      status: "completed",
      detail: "Tabular features and velocity historical vectors retrieved",
    },
    {
      step: "02",
      title: "Risk explanation inspected",
      status: "completed",
      detail: "Tree SHAP feature attributions and local SHAP values verified",
    },
    {
      step: "03",
      title: "Related entities queried",
      status: "completed",
      detail: "2-hop cross-transaction bipartite graph traversal executed",
    },
    {
      step: "04",
      title: "FraudDNA cluster analyzed",
      status: "completed",
      detail: "Entity connectivity ring and shared device velocity evaluated",
    },
    {
      step: "05",
      title: "Historical policy evidence retrieved",
      status: "completed",
      detail: "Grounded guidelines matched via semantic cosine vector search",
    },
    {
      step: "06",
      title: "Findings synthesized",
      status: "completed",
      detail: "Bounded structured case findings produced for deterministic policy engine",
    },
  ];

  const items: StepItem[] = Array.isArray(steps) ? steps : defaultSteps;

  return (
    <div className="space-y-3 relative before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-[1px] before:bg-[#1C1D22]">
      {items.map((item, idx) => {
        const isDone = typeof steps === "number" ? idx < steps : idx < currentStep;
        return (
          <div key={idx} className="relative flex items-start gap-3 pl-0">
            <div
              className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 z-10 border text-[10px] font-mono ${
                isDone
                  ? "bg-[#121317] border-[#CC9166] text-[#CC9166]"
                  : "bg-[#08080A] border-[#1C1D22] text-[#777A88]"
              }`}
            >
              {item.step}
            </div>
            <div className="pt-0.5">
              <p className="text-xs font-mono text-[#FFFFFF] font-medium">
                {item.title}
              </p>
              {item.detail && (
                <p className="text-[11px] text-[#777A88] font-sans mt-0.5 leading-relaxed">
                  {item.detail}
                </p>
              )}
            </div>
          </div>
        );
      })}

      {toolTrace && toolTrace.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[#1C1D22]/60">
          <div className="text-[10px] font-mono text-[#5E616E] uppercase mb-2">
            Tool Provenance Trace
          </div>
          <div className="space-y-1">
            {toolTrace.map((t, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-[11px] font-mono px-2 py-1 rounded bg-[#121317] border border-[#1C1D22]"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      t.status === "success" ? "bg-[#8FAF9B]" : "bg-[#D05B5B]"
                    }`}
                  />
                  <span className="text-[#E2E3E9]">{t.tool_name}</span>
                </div>
                <span className="text-[#777A88] text-[10px]">
                  {t.duration_ms ? `${Math.round(t.duration_ms)}ms` : "cached"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── EvidenceCard ────────────────────────────────────────────
export function EvidenceCard({
  sourceId,
  title,
  snippet,
  score,
  docType,
  documentType,
}: {
  sourceId: string;
  title: string;
  snippet: string;
  score?: number;
  docType?: string;
  documentType?: string;
}) {
  const displayDocType = documentType || docType || "POLICY DIRECTIVE";

  return (
    <div className="bg-[#121317] border border-[#1C1D22] hover:border-[#2E3038] rounded-[8px] p-3.5 transition-colors">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="font-mono text-[11px] font-semibold text-[#CC9166] tracking-wide px-2 py-0.5 rounded bg-[#CC9166]/10 border border-[#CC9166]/30">
          {sourceId}
        </span>
        {score !== undefined && (
          <span className="text-[10px] font-mono text-[#9194A1] bg-[#08080A] px-2 py-0.5 rounded border border-[#1C1D22]">
            RELEVANCE {(score * 100).toFixed(1)}%
          </span>
        )}
      </div>
      <h4 className="text-xs font-medium text-[#FFFFFF] mb-1 font-sans">{title}</h4>
      <p className="text-[11px] text-[#9194A1] font-sans leading-relaxed line-clamp-3">
        {snippet}
      </p>
      <div className="mt-2.5 pt-2 border-t border-[#1C1D22] flex items-center justify-between text-[10px] text-[#777A88] font-mono">
        <span>DIRECTIVE: {displayDocType}</span>
        <span className="flex items-center gap-1 text-[#8FAF9B]">
          <CheckCircle2 className="h-3 w-3" /> VERIFIED SOURCE
        </span>
      </div>
    </div>
  );
}

// ─── PolicyDecisionCard ──────────────────────────────────────
export function PolicyDecisionCard({
  action,
  reasonCodes = [],
  policyVersion = "2026.1",
  isDeterministic = true,
  evidenceSummary,
}: {
  action: string;
  reasonCodes?: string[];
  policyVersion?: string;
  isDeterministic?: boolean;
  evidenceSummary?: string[];
}) {
  return (
    <div className="bg-[#040406] rounded-[10px] border border-[#1C1D22] p-5 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono text-[#9194A1] uppercase tracking-wider flex items-center gap-1.5">
          <Scale className="h-3.5 w-3.5 text-[#CC9166]" />
          DECISION ENGINE
        </span>
        <span className="text-[10px] font-mono text-[#777A88]">
          v{policyVersion}
        </span>
      </div>

      <div className="flex items-center justify-between py-2 border-y border-[#1C1D22]">
        <div>
          <p className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">ACTION ENFORCED</p>
          <p className="font-serif text-3xl text-[#FFFFFF] tracking-tight mt-0.5">
            {action}
          </p>
        </div>
        <DecisionBadge action={action} size="lg" />
      </div>

      {reasonCodes.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">REASONS</p>
          <div className="flex flex-wrap gap-1.5">
            {reasonCodes.map((code, idx) => (
              <span
                key={idx}
                className="text-[10px] font-mono px-2.5 py-1 bg-[#121317] border border-[#1C1D22] text-[#E2E3E9] rounded font-medium"
              >
                {code.toUpperCase().replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {evidenceSummary && evidenceSummary.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <p className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">DECISION RATIONALE</p>
          <ul className="space-y-1 text-xs text-[#9194A1] font-sans">
            {evidenceSummary.map((item, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-[#CC9166] mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="pt-2 border-t border-[#1C1D22] flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-1.5 text-[#9194A1]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#CC9166]" />
          <span>Decision authority: policy controls</span>
        </div>
        <span className="font-mono text-[#8FAF9B] text-[10px]">
          {isDeterministic ? "Deterministic Enforced" : "Policy Monitored"}
        </span>
      </div>
    </div>
  );
}

// ─── LoadingSkeleton ─────────────────────────────────────────
export function LoadingSkeleton({
  lines = 3,
  className = "",
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={`space-y-2.5 animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-[#121317] border border-[#1C1D22] rounded-md"
          style={{ width: `${85 - i * 15}%` }}
        />
      ))}
    </div>
  );
}

// ─── LoadingState ────────────────────────────────────────────
export function LoadingState({ message = "Retrieving risk intelligence..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="h-8 w-8 rounded-full border border-[#2E3038] border-t-[#CC9166] animate-spin" />
      <p className="text-xs font-mono text-[#9194A1] tracking-wider uppercase">{message}</p>
    </div>
  );
}

// ─── ErrorState ──────────────────────────────────────────────
export function ErrorState({
  title = "Risk Intelligence Unavailable",
  error,
  onRetry,
}: {
  title?: string;
  error: string;
  onRetry?: () => void;
}) {
  return (
    <div className="bg-[#040406] border border-[#D05B5B]/30 rounded-[10px] p-8 text-center space-y-3">
      <div className="h-9 w-9 rounded-full bg-[#D05B5B]/10 border border-[#D05B5B]/30 flex items-center justify-center text-[#D05B5B] mx-auto">
        <AlertTriangle className="h-4 w-4" />
      </div>
      <div>
        <h4 className="text-xs font-mono uppercase tracking-wider text-[#FFFFFF]">
          {title}
        </h4>
        <p className="text-xs text-[#9194A1] font-sans mt-1 max-w-md mx-auto">{error}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-1.5 text-xs font-mono rounded-full bg-[#121317] border border-[#2E3038] text-[#FFFFFF] hover:border-[#CC9166] transition-colors"
        >
          RETRY QUERY
        </button>
      )}
    </div>
  );
}

// ─── EmptyState ──────────────────────────────────────────────
export function EmptyState({
  title = "No data records identified",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode | { label: string; onClick: () => void };
}) {
  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-[10px] py-16 px-6 text-center space-y-2 text-[#777A88]">
      <div className="h-8 w-8 rounded-full bg-[#121317] border border-[#1C1D22] flex items-center justify-center mx-auto text-sm">
        ∅
      </div>
      <p className="text-xs font-mono uppercase tracking-wider text-[#E2E3E9]">{title}</p>
      {description && <p className="text-xs text-[#777A88] max-w-sm mx-auto">{description}</p>}
      {action && (
        <div className="pt-2">
          {typeof action === "object" && action !== null && "label" in action && typeof (action as { label: string }).label === "string" ? (
            <button
              onClick={(action as { onClick: () => void }).onClick}
              className="px-3 py-1.5 text-xs font-mono rounded-md bg-[#121317] border border-[#1C1D22] text-[#E2E3E9] hover:border-[#CC9166] transition-colors"
            >
              {(action as { label: string }).label}
            </button>
          ) : (
            action as ReactNode
          )}
        </div>
      )}
    </div>
  );
}

// ─── Formatters ──────────────────────────────────────────────
export function formatINR(value: number): string {
  if (value >= 10_000_000) return `₹${(value / 10_000_000).toFixed(2)}Cr`;
  if (value >= 100_000) return `₹${(value / 100_000).toFixed(2)}L`;
  if (value >= 1_000) return `₹${(value / 1_000).toFixed(1)}K`;
  return `₹${value.toFixed(0)}`;
}

export function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-IN");
}
