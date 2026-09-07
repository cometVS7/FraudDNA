import React from "react";
import { X } from "lucide-react";
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
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0D0E12] border-l border-[#1C1D22] shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="flex items-center justify-between p-5 border-b border-[#1C1D22] bg-[#08080A]">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
            ENTITY FORENSICS
          </div>
          <h2 className="text-lg font-serif text-white mt-0.5 capitalize flex items-center gap-2">
            <span>{entityType} Profile</span>
          </h2>
          <div className="font-mono text-xs text-[#9194A1] mt-0.5">{entityId}</div>
        </div>
        <button
          onClick={onClose}
          className="text-[#777A88] hover:text-white p-1 rounded transition-colors"
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
            <div className="grid grid-cols-2 gap-3 bg-[#040406] border border-[#1C1D22] rounded-lg p-3">
              <div>
                <div className="text-[10px] font-mono text-[#777A88] uppercase">Entity Risk</div>
                <div
                  className={`text-xl font-serif mt-0.5 font-medium ${
                    profile.risk_score >= 0.7
                      ? "text-[#D05B5B]"
                      : profile.risk_score >= 0.35
                      ? "text-[#C47A63]"
                      : "text-[#34D399]"
                  }`}
                >
                  {profile.risk_score.toFixed(3)}
                </div>
                <span className="text-[9px] font-mono text-[#5E616E] uppercase">
                  {profile.risk_tier} TIER
                </span>
              </div>

              <div>
                <div className="text-[10px] font-mono text-[#777A88] uppercase">Status</div>
                <div className="text-sm font-mono text-white mt-1 font-semibold">
                  {profile.status}
                </div>
                <span className="text-[9px] font-mono text-[#5E616E]">Active in graph</span>
              </div>
            </div>

            {/* Behavioral & Historical Metrics */}
            <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#CC9166] font-semibold border-b border-[#1C1D22] pb-1.5">
                Behavioral Velocity & History
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-[10px] font-mono text-[#5E616E]">First Seen</div>
                  <div className="font-mono text-white mt-0.5 text-[11px]">
                    {profile.first_seen ? new Date(profile.first_seen).toLocaleDateString("en-IN") : "—"}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono text-[#5E616E]">Last Active</div>
                  <div className="font-mono text-white mt-0.5 text-[11px]">
                    {profile.last_seen ? new Date(profile.last_seen).toLocaleDateString("en-IN") : "—"}
                  </div>
                </div>

                {profile.lifetime_transaction_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E]">Lifetime Tx Count</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {profile.lifetime_transaction_count}
                    </div>
                  </div>
                )}

                {profile.lifetime_volume_inr !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E]">Lifetime Volume</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {formatINR(profile.lifetime_volume_inr)}
                    </div>
                  </div>
                )}

                {profile.distinct_devices_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E]">Linked Devices</div>
                    <div className="font-mono text-white mt-0.5 text-sm font-semibold">
                      {profile.distinct_devices_count}
                    </div>
                  </div>
                )}

                {profile.distinct_cards_count !== undefined && (
                  <div>
                    <div className="text-[10px] font-mono text-[#5E616E]">Linked Cards</div>
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
      <div className="p-4 border-t border-[#1C1D22] bg-[#08080A] flex items-center justify-end">
        <button
          onClick={onClose}
          className="px-4 py-1.5 text-xs text-[#9194A1] hover:text-white rounded border border-[#1C1D22] hover:bg-[#121317] transition-colors"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
