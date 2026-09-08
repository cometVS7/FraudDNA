"use client";

import React, { useState } from "react";
import { X, Search, ArrowRight, AlertTriangle, Route } from "lucide-react";
import { searchNetworkPaths } from "@/lib/api";
import type { NetworkPath } from "@/types/network";

interface PathSearchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSourceId?: string;
  defaultTargetId?: string;
}

export function PathSearchDialog({
  isOpen,
  onClose,
  defaultSourceId = "",
  defaultTargetId = "",
}: PathSearchDialogProps) {
  const [sourceId, setSourceId] = useState(defaultSourceId);
  const [targetId, setTargetId] = useState(defaultTargetId);
  const [maxDepth, setMaxDepth] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paths, setPaths] = useState<NetworkPath[]>([]);
  const [searched, setSearched] = useState(false);

  if (!isOpen) return null;

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!sourceId.trim() || !targetId.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const resp = await searchNetworkPaths({
        source_id: sourceId.trim(),
        target_id: targetId.trim(),
        max_depth: Math.min(maxDepth, 3), // Safety bounded to <= 3
        max_paths: 10,
      });
      setPaths(resp.paths || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to find connection paths");
      setPaths([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#0D0F14] border border-white/[0.08] rounded-xl w-full max-w-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] bg-[#0A0C10]">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-[#CC9166]/15 border border-[#CC9166]/40 flex items-center justify-center text-[#CC9166]">
              <Route className="h-4 w-4" />
            </div>
            <div>
              <div className="text-[10px] font-mono tracking-widest text-[#CC9166] uppercase font-semibold">
                MULTI-HOP TRAVERSAL
              </div>
              <h2 className="text-base font-serif text-white">Path Search Intelligence</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#777A88] hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
                  Source Entity ID
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. cust_00843"
                  value={sourceId}
                  onChange={(e) => setSourceId(e.target.value)}
                  className="w-full bg-[#14161F] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#CC9166] transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono text-[#777A88] uppercase mb-1">
                  Target Entity ID
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. dev_d0339"
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className="w-full bg-[#14161F] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#CC9166] transition-colors"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2 text-xs text-[#777A88]">
                <span>Traversal Depth:</span>
                <select
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(Number(e.target.value))}
                  className="bg-[#14161F] border border-white/[0.08] rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-[#CC9166]"
                >
                  <option value={1}>1 hop</option>
                  <option value={2}>2 hops</option>
                  <option value={3}>3 hops (Max Bounded)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || !sourceId.trim() || !targetId.trim()}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#CC9166] text-[#08080A] font-bold text-xs hover:bg-[#CC9166]/90 disabled:opacity-40 transition-all shadow-md"
              >
                <Search className="h-3.5 w-3.5" />
                <span>{loading ? "Traversing..." : "Discover Paths"}</span>
              </button>
            </div>
          </form>

          {error && (
            <div className="p-3 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 text-xs text-[#EF4444] flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Path Results */}
          {searched && !loading && (
            <div className="border-t border-white/[0.06] pt-4 space-y-3">
              <div className="text-[10px] font-mono text-[#777A88] uppercase tracking-wider">
                Ranked Traversal Paths Found ({paths.length})
              </div>

              {paths.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#777A88] bg-[#0A0C10] rounded-lg border border-white/[0.04]">
                  No graph paths found connecting {sourceId} and {targetId} within {maxDepth} hops.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {paths.map((p, idx) => (
                    <div
                      key={p.path_id || idx}
                      className="p-3 bg-[#0A0C10] border border-white/[0.06] rounded-lg space-y-1.5 text-xs font-mono"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[#CC9166] font-semibold">Path #{idx + 1}</span>
                        <span className="text-[10px] text-[#777A88]">
                          {p.length} hops • Risk: {p.risk_score.toFixed(3)}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#E2E3E9] flex items-center gap-1.5 flex-wrap">
                        {p.nodes.map((node, nIdx) => (
                          <React.Fragment key={nIdx}>
                            <span className="px-1.5 py-0.5 rounded bg-[#14161F] border border-white/[0.06]">
                              {node}
                            </span>
                            {nIdx < p.nodes.length - 1 && (
                              <ArrowRight className="h-3 w-3 text-[#5E616E]" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
