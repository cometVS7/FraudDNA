"use client";

import React from "react";
import type { Transaction } from "@/lib/api";
import { formatINR } from "@/components/ui";
import {
  CreditCard,
  Smartphone,
  Globe,
  Store,
  User,
  Clock,
  ChevronRight,
  Activity,
  Tag,
} from "lucide-react";

interface TransactionLedgerProps {
  transaction: Transaction | null;
  loading?: boolean;
  onOpenEntity: (entityType: string, entityId: string) => void;
}

export function TransactionLedger({
  transaction,
  loading = false,
  onOpenEntity,
}: TransactionLedgerProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl">
        <div className="h-4 w-32 bg-[#1C1D22] animate-pulse rounded" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-[#12141A] animate-pulse rounded-lg border border-white/[0.04]" />
          ))}
        </div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 text-center text-xs text-[#777A88]">
        No transaction facts loaded.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      {/* Header */}
      <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
            <Activity className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              FACTS & INFRASTRUCTURE
            </div>
            <h3 className="text-sm font-serif text-white font-normal">
              Transaction Ledger
            </h3>
          </div>
        </div>
      </div>

      <div className="space-y-3.5 text-xs font-sans">
        {/* Amount & Time */}
        <div className="grid grid-cols-2 gap-3 bg-[#12141A] p-3 rounded-lg border border-white/[0.06]">
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase">AMOUNT</div>
            <div className="text-xl font-serif text-white font-medium mt-0.5">
              {formatINR(transaction.amount)}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-mono text-[#777A88] uppercase flex items-center gap-1">
              <Clock className="h-3 w-3 text-[#5E616E]" />
              <span>TIMESTAMP (IST)</span>
            </div>
            <div className="font-mono text-[11px] text-[#E2E3E9] mt-1 truncate">
              {transaction.timestamp
                ? new Date(transaction.timestamp).toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  }) +
                  " " +
                  new Date(transaction.timestamp).toLocaleDateString("en-IN")
                : "—"}
            </div>
          </div>
        </div>

        {/* Customer Entity Chip */}
        <div
          onClick={() => onOpenEntity("customer", transaction.customer_id)}
          className="flex items-center justify-between p-2.5 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] hover:border-[#CC9166]/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-7 w-7 rounded-md bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166] flex-shrink-0">
              <User className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#777A88] uppercase">Customer</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#CC9166] transition-colors">
                {transaction.customer_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#CC9166] group-hover:translate-x-0.5 transition-all" />
        </div>

        {/* Card Entity Chip */}
        <div
          onClick={() => onOpenEntity("card", transaction.card_id)}
          className="flex items-center justify-between p-2.5 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] hover:border-[#60A5FA]/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-7 w-7 rounded-md bg-[#60A5FA]/15 flex items-center justify-center text-[#60A5FA] flex-shrink-0">
              <CreditCard className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#777A88] uppercase">Payment Card</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#60A5FA] transition-colors">
                {transaction.card_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#60A5FA] group-hover:translate-x-0.5 transition-all" />
        </div>

        {/* Device Entity Chip */}
        <div
          onClick={() => onOpenEntity("device", transaction.device_id)}
          className="flex items-center justify-between p-2.5 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] hover:border-[#A78BFA]/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-7 w-7 rounded-md bg-[#A78BFA]/15 flex items-center justify-center text-[#A78BFA] flex-shrink-0">
              <Smartphone className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#777A88] uppercase">Device Fingerprint</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#A78BFA] transition-colors">
                {transaction.device_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#A78BFA] group-hover:translate-x-0.5 transition-all" />
        </div>

        {/* IP Address Entity Chip */}
        <div
          onClick={() => onOpenEntity("ip", transaction.ip_address)}
          className="flex items-center justify-between p-2.5 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] hover:border-[#34D399]/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-7 w-7 rounded-md bg-[#34D399]/15 flex items-center justify-center text-[#34D399] flex-shrink-0">
              <Globe className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#777A88] uppercase">IP Address</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#34D399] transition-colors">
                {transaction.ip_address}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#34D399] group-hover:translate-x-0.5 transition-all" />
        </div>

        {/* Merchant Entity Chip */}
        <div
          onClick={() => onOpenEntity("merchant", transaction.merchant_id)}
          className="flex items-center justify-between p-2.5 rounded-lg bg-[#12141A] hover:bg-[#181A22] border border-white/[0.06] hover:border-[#EAB308]/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-7 w-7 rounded-md bg-[#EAB308]/15 flex items-center justify-center text-[#EAB308] flex-shrink-0">
              <Store className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#777A88] uppercase">Merchant ID</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#EAB308] transition-colors">
                {transaction.merchant_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#EAB308] group-hover:translate-x-0.5 transition-all" />
        </div>

        {/* Cluster Context */}
        {transaction.cluster_id && (
          <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono">
            <span className="text-[#777A88] flex items-center gap-1">
              <Tag className="h-3 w-3 text-[#D05B5B]" />
              <span>Assigned Cluster:</span>
            </span>
            <span className="text-[#D05B5B] font-semibold bg-[#D05B5B]/10 px-2 py-0.5 rounded border border-[#D05B5B]/30">
              {transaction.cluster_id}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
