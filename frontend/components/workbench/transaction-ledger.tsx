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
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4">
        <div className="text-center py-8 text-xs text-[#777A88]">Loading transaction facts...</div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 text-center text-xs text-[#777A88]">
        No transaction facts loaded.
      </div>
    );
  }

  return (
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-4 shadow-xl">
      <div className="border-b border-[#1C1D22] pb-2.5 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            FACTS & INFRASTRUCTURE
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Transaction Ledger
          </h3>
        </div>
      </div>

      <div className="space-y-3.5 text-xs font-sans">
        {/* Amount */}
        <div>
          <div className="text-[10px] font-mono text-[#5E616E] uppercase">Transaction Amount</div>
          <div className="text-xl font-serif text-white mt-0.5 font-medium">
            {formatINR(transaction.amount)}
          </div>
        </div>

        {/* Timestamp */}
        <div className="flex items-start gap-2 pt-2 border-t border-[#1C1D22]/60">
          <Clock className="h-3.5 w-3.5 text-[#5E616E] mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-mono text-[#5E616E]">Timestamp (UTC / IST)</div>
            <div className="font-mono text-[11px] text-[#E2E3E9] truncate">
              {transaction.timestamp
                ? new Date(transaction.timestamp).toLocaleString("en-IN")
                : "—"}
            </div>
          </div>
        </div>

        {/* Customer */}
        <div
          onClick={() => onOpenEntity("customer", transaction.customer_id)}
          className="flex items-center justify-between p-2 rounded bg-[#121317]/60 hover:bg-[#121317] border border-[#1C1D22] cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <User className="h-3.5 w-3.5 text-[#CC9166] flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#5E616E] uppercase">Customer</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#CC9166]">
                {transaction.customer_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#CC9166] transition-colors" />
        </div>

        {/* Card */}
        <div
          onClick={() => onOpenEntity("card", transaction.card_id)}
          className="flex items-center justify-between p-2 rounded bg-[#121317]/60 hover:bg-[#121317] border border-[#1C1D22] cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <CreditCard className="h-3.5 w-3.5 text-[#60A5FA] flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#5E616E] uppercase">Payment Card</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#60A5FA]">
                {transaction.card_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#60A5FA] transition-colors" />
        </div>

        {/* Device */}
        <div
          onClick={() => onOpenEntity("device", transaction.device_id)}
          className="flex items-center justify-between p-2 rounded bg-[#121317]/60 hover:bg-[#121317] border border-[#1C1D22] cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Smartphone className="h-3.5 w-3.5 text-[#A78BFA] flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#5E616E] uppercase">
                Device Fingerprint
              </div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#A78BFA]">
                {transaction.device_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#A78BFA] transition-colors" />
        </div>

        {/* IP Address */}
        <div
          onClick={() => onOpenEntity("ip", transaction.ip_address)}
          className="flex items-center justify-between p-2 rounded bg-[#121317]/60 hover:bg-[#121317] border border-[#1C1D22] cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Globe className="h-3.5 w-3.5 text-[#34D399] flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#5E616E] uppercase">IP Address</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#34D399]">
                {transaction.ip_address}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#34D399] transition-colors" />
        </div>

        {/* Merchant */}
        <div
          onClick={() => onOpenEntity("merchant", transaction.merchant_id)}
          className="flex items-center justify-between p-2 rounded bg-[#121317]/60 hover:bg-[#121317] border border-[#1C1D22] cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Store className="h-3.5 w-3.5 text-[#EAB308] flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-[9px] font-mono text-[#5E616E] uppercase">Merchant ID</div>
              <div className="font-mono text-[11px] text-[#E2E3E9] truncate group-hover:text-[#EAB308]">
                {transaction.merchant_id}
              </div>
            </div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-[#5E616E] group-hover:text-[#EAB308] transition-colors" />
        </div>

        {/* Cluster Context */}
        {transaction.cluster_id && (
          <div className="pt-2 border-t border-[#1C1D22]/60">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-[#5E616E]">Assigned Risk Cluster:</span>
              <span className="text-[#D05B5B] font-semibold">{transaction.cluster_id}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
