"use client";

import React from "react";
import { X, User, Activity } from "lucide-react";
import { useAsync } from "@/hooks/use-async";
import { fetchEntityProfile } from "@/lib/api";
import { formatINR } from "@/components/ui";
import type { EntityProfileResponse } from "@/lib/api";

interface EntityProfileDrawerProps {
  entityType: string | null;
  entityId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectTransaction?: (txId: string) => void;
}

export function EntityProfileDrawer({
  entityType,
  entityId,
  isOpen,
  onClose,
}: EntityProfileDrawerProps) {
  const profileData = useAsync<EntityProfileResponse | null>(
    () =>
      entityType && entityId
        ? fetchEntityProfile(entityType, entityId).catch(() => null)
        : Promise.resolve(null),
    [entityType, entityId]
  );

  if (!isOpen || !entityType || !entityId) return null;

  const profile = profileData.status === "success" ? profileData.data : null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0D0F14] border-l border-white/[0.08] shadow-2xl flex flex-col animate-in slide-in-from-right duration-200 backdrop-blur-2xl">
      {/* Drawer Header */}
      <div className="flex items-center justify-between p-5 border-b border-white/[0.06] bg-[#0A0C10]">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
            <User className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] font-mono tracking-widest text-[#CC9166] uppercase font-semibold">
              ENTITY FORENSICS
            </div>
            <h2 className="text-base font-serif text-white capitalize">
              {entityType} Profile
            </h2>
            <div className="font-mono text-xs text-[#9194A1]">{entityId}</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-[#777A88] hover:text-white p-1.5 rounded-lg hover:bg-[#181A22] transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {profileData.status === "loading" && (
          <div className="py-12 text-center text-xs text-[#777A88]">
            Loading entity intelligence...
          </div>
        )}

        {profile && (
          <div className="space-y-5">
            {/* Risk & Status Banner */}
            <div className="grid grid-cols-2 gap-3 bg-[#0A0C10] border border-white/[0.06] rounded-xl p-4">
              <div>
                <div className="text-[10px] font-mono text-[#777A88] uppercase">Entity Risk Score</div>
                <div
                  className={`text-2xl font-serif mt-0.5 font-medium ${
                    profile.risk_score >= 0.7
                      ? "text-[#EF4444]"
                      : profile.risk_score >= 0.35
                      ? "text-[#F97316]"
                      : "text-[#10B981]"
                  }`}
                >
                  {profile.risk_score.toFixed(3)}
                </div>
                <span className="text-[9px] font-mono text-[#5E616E] uppercase">
                  {profile.risk_tier} TIER
                </span>
              </div>

              <div>
                <div className="text-[10px] font-mono text-[#777A88] uppercase">Graph Status</div>
                <div className="text-sm font-mono text-white mt-1 font-semibold">
                  {profile.status}
                </div>
                <span className="text-[9px] font-mono text-[#10B981] flex items-center gap-1 mt-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#10B981]" />
                  <span>Active in FraudDNA</span>
                </span>
              </div>
            </div>

            {/* Behavioral & Historical Metrics */}
            <div className="bg-[#0A0C10] border border-white/[0.06] rounded-xl p-4 space-y-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#CC9166] font-semibold border-b border-white/[0.06] pb-2 flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" />
                <span>Behavioral Velocity & Telemetry</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-[10px] font-mono text-[#777A88]">First Observed</div>
                  <div className="font-mono text-white mt-0.5 text-[11px]">
                    {profile.first_seen ? new Date(profile.first_seen).toLocaleDateString("en-IN") : "—"}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono text-[#777A88]">Last Observed</div>
                  <div className="font-mono text-white mt-0.5 text-[11px]">
                    {profile.last_seen ? new Date(profile.last_seen).toLocaleDateString("en-IN") : "—"}
                  </div>
                </div>

                {profile.lifetime_transaction_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#777A88]">Lifetime Count</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {profile.lifetime_transaction_count}
                    </div>
                  </div>
                )}

                {profile.lifetime_volume_inr !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#777A88]">Lifetime Volume</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {formatINR(profile.lifetime_volume_inr)}
                    </div>
                  </div>
                )}

                {profile.distinct_devices_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#777A88]">Linked Devices</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {profile.distinct_devices_count}
                    </div>
                  </div>
                )}

                {profile.distinct_cards_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#777A88]">Linked Cards</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {profile.distinct_cards_count}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-white/[0.06] bg-[#0A0C10] flex items-center justify-end">
        <button
          onClick={onClose}
          className="px-4 py-1.5 text-xs font-mono text-[#9194A1] hover:text-white rounded-lg border border-white/[0.08] hover:bg-[#14161F] transition-colors"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
