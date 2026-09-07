"use client";

import React, { useState } from "react";
import { X, Search, ArrowRight, AlertTriangle } from "lucide-react";
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
        max_depth: maxDepth,
        max_paths: 5,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#0D0E12] border border-[#1C1D22] rounded-lg w-full max-w-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1C1D22] bg-[#08080A]">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              MULTI-HOP GRAPH TRAVERSAL
            </div>
            <h2 className="text-lg font-serif text-white mt-0.5">Connection Path Search</h2>
          </div>
          <button
            onClick={onClose}
            className="text-[#777A88] hover:text-white p-1 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

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
                  className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166]"
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
                  className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#CC9166]"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2 text-xs text-[#777A88]">
                <span>Max Hops (Depth):</span>
                <select
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(Number(e.target.value))}
                  className="bg-[#121317] border border-[#1C1D22] rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-[#CC9166]"
                >
                  <option value={1}>1 hop</option>
                  <option value={2}>2 hops</option>
                  <option value={3}>3 hops</option>
                  <option value={4}>4 hops</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || !sourceId.trim() || !targetId.trim()}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-[#CC9166] text-[#08080A] font-medium text-xs hover:bg-[#CC9166]/90 disabled:opacity-40 transition-opacity"
              >
                <Search className="h-3.5 w-3.5" />
                <span>{loading ? "Searching..." : "Find Paths"}</span>
              </button>
            </div>
          </form>

          {error && (
            <div className="p-3 rounded bg-[#D05B5B]/10 border border-[#D05B5B]/30 text-xs text-[#D05B5B] flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Path Results */}
          {searched && !loading && (
            <div className="border-t border-[#1C1D22] pt-4 space-y-3">
              <div className="text-[10px] font-mono text-[#777A88] uppercase">
                Ranked Traversal Paths Found ({paths.length})
              </div>

              {paths.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#777A88]">
                  No graph paths found connecting {sourceId} and {targetId} within {maxDepth} hops.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {paths.map((p, idx) => (
                    <div
                      key={p.path_id || idx}
                      className="p-3 bg-[#040406] border border-[#1C1D22] rounded space-y-1.5 text-xs font-mono"
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
                            <span className="px-1.5 py-0.5 rounded bg-[#121317] border border-[#1C1D22]">
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
