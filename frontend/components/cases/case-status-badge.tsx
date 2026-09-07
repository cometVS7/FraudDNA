import React from "react";
import type { CasePriority, CaseStatus } from "@/types/case";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Flame,
  HelpCircle,
  MinusCircle,
  ShieldAlert,
} from "lucide-react";

interface CaseStatusBadgeProps {
  status: CaseStatus | string;
  size?: "sm" | "md";
}

export function CaseStatusBadge({ status, size = "sm" }: CaseStatusBadgeProps) {
  const norm = (status || "").toUpperCase();

  let colorClass = "bg-[#1C1D22] text-[#9194A1] border-[#2E3038]";
  let Icon = HelpCircle;

  switch (norm) {
    case "NEW":
      colorClass = "bg-[#3B82F6]/10 text-[#60A5FA] border-[#3B82F6]/30";
      Icon = Clock;
      break;
    case "IN_REVIEW":
      colorClass = "bg-[#8B5CF6]/10 text-[#A78BFA] border-[#8B5CF6]/30";
      Icon = AlertCircle;
      break;
    case "ESCALATED":
      colorClass = "bg-[#D05B5B]/15 text-[#D05B5B] border-[#D05B5B]/40";
      Icon = ShieldAlert;
      break;
    case "RESOLVED":
      colorClass = "bg-[#10B981]/15 text-[#34D399] border-[#10B981]/30";
      Icon = CheckCircle2;
      break;
    case "CLOSED":
      colorClass = "bg-[#2E3038]/40 text-[#777A88] border-[#2E3038]";
      Icon = MinusCircle;
      break;
  }

  const paddingClass = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";
  const iconSize = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded-full border ${paddingClass} ${colorClass}`}
    >
      <Icon className={iconSize} />
      <span>{norm.replace("_", " ")}</span>
    </span>
  );
}

interface CasePriorityBadgeProps {
  priority: CasePriority | string;
  size?: "sm" | "md";
}

export function CasePriorityBadge({ priority, size = "sm" }: CasePriorityBadgeProps) {
  const norm = (priority || "").toUpperCase();

  let colorClass = "text-[#9194A1] bg-[#1C1D22] border-[#2E3038]";
  let Icon = MinusCircle;

  switch (norm) {
    case "CRITICAL":
      colorClass = "text-[#D05B5B] bg-[#D05B5B]/15 border-[#D05B5B]/40";
      Icon = Flame;
      break;
    case "HIGH":
      colorClass = "text-[#C47A63] bg-[#C47A63]/15 border-[#C47A63]/30";
      Icon = AlertTriangle;
      break;
    case "MEDIUM":
      colorClass = "text-[#EAB308] bg-[#EAB308]/15 border-[#EAB308]/30";
      Icon = AlertCircle;
      break;
    case "LOW":
      colorClass = "text-[#34D399] bg-[#10B981]/10 border-[#10B981]/20";
      Icon = CheckCircle2;
      break;
  }

  const paddingClass = size === "sm" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[10px]";
  const iconSize = size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3";

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono uppercase tracking-wider rounded border ${paddingClass} ${colorClass}`}
    >
      <Icon className={iconSize} />
      <span>{norm}</span>
    </span>
  );
}
