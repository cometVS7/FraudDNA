"use client";

import { ReactNode } from "react";

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
  variant?: "default" | "success" | "warning" | "danger" | "info";
}) {
  const borderColors: Record<string, string> = {
    default: "border-border",
    success: "border-risk-allow/30",
    warning: "border-risk-review/30",
    danger: "border-risk-hold/30",
    info: "border-blue-200",
  };

  return (
    <div
      className={`bg-card rounded-xl border ${borderColors[variant]} p-5 shadow-sm hover:shadow-md transition-shadow duration-200`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <p className="text-2xl font-bold tracking-tight text-foreground">{value}</p>
      {sublabel && (
        <p className="text-xs text-muted-foreground mt-1">{sublabel}</p>
      )}
      {trend && (
        <p className="text-xs text-muted-foreground mt-1 font-mono">{trend}</p>
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
  const colors: Record<string, string> = {
    low: "bg-emerald-50 text-emerald-700 border-emerald-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
    high: "bg-orange-50 text-orange-700 border-orange-200",
    critical: "bg-red-50 text-red-700 border-red-200",
    allow: "bg-emerald-50 text-emerald-700 border-emerald-200",
    review: "bg-amber-50 text-amber-700 border-amber-200",
    hold: "bg-red-50 text-red-700 border-red-200",
  };

  const sizes: Record<string, string> = {
    xs: "text-[10px] px-1.5 py-0.5",
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
  };

  const key = level.toLowerCase();
  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${colors[key] || colors.low} ${sizes[size]}`}
    >
      {level.toUpperCase()}
    </span>
  );
}

// ─── DecisionBadge ───────────────────────────────────────────
export function DecisionBadge({ action }: { action: string }) {
  const colors: Record<string, string> = {
    ALLOW: "bg-emerald-600 text-white",
    REVIEW: "bg-amber-500 text-white",
    HOLD: "bg-red-600 text-white",
  };

  return (
    <span
      className={`inline-flex items-center rounded-lg px-4 py-2 text-sm font-bold tracking-wider ${colors[action] || "bg-gray-500 text-white"}`}
    >
      {action}
    </span>
  );
}

// ─── LoadingState ────────────────────────────────────────────
export function LoadingState({ message = "Loading data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

// ─── ErrorState ──────────────────────────────────────────────
export function ErrorState({
  error,
  onRetry,
}: {
  error: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 bg-red-50/50 rounded-xl border border-red-100">
      <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 text-lg font-bold">
        !
      </div>
      <p className="text-sm text-red-600 font-medium">Error loading data</p>
      <p className="text-xs text-red-500 max-w-md text-center">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 px-4 py-1.5 text-xs font-medium rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

// ─── EmptyState ──────────────────────────────────────────────
export function EmptyState({
  title = "No data available",
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-muted-foreground">
      <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center text-lg">
        ∅
      </div>
      <p className="text-sm font-medium">{title}</p>
      {description && <p className="text-xs">{description}</p>}
    </div>
  );
}

// ─── SectionCard ─────────────────────────────────────────────
export function SectionCard({
  title,
  subtitle,
  children,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-card rounded-xl border border-border shadow-sm ${className}`}>
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
        )}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

// ─── DataLabel ───────────────────────────────────────────────
export function DataLabel({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground font-mono px-2 py-0.5 rounded bg-muted/60 border border-border/50">
      {label}
    </span>
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
