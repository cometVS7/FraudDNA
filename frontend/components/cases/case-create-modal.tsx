"use client";

import React, { useState } from "react";
import { X, Plus, AlertTriangle } from "lucide-react";
import { createCase } from "@/lib/api";
import type { CasePriority, CaseResponse } from "@/types/case";

interface CaseCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (newCase: CaseResponse) => void;
  initialTransactionId?: string;
  initialTitle?: string;
}

export function CaseCreateModal({
  isOpen,
  onClose,
  onCreated,
  initialTransactionId = "",
  initialTitle = "",
}: CaseCreateModalProps) {
  const [title, setTitle] = useState(
    initialTitle || (initialTransactionId ? `Investigation Case for ${initialTransactionId}` : "")
  );
  const [priority, setPriority] = useState<CasePriority>("MEDIUM");
  const [owner, setOwner] = useState("analyst_01");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Case title is required.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const resp = await createCase({
        title: title.trim(),
        priority,
        owner: owner.trim() || null,
        notes: notes.trim() || null,
        investigation_id: initialTransactionId ? `inv_${initialTransactionId}` : null,
      });
      onCreated(resp);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#0D0E12] border border-[#1C1D22] rounded-lg w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1C1D22] bg-[#08080A]">
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-[#CC9166] uppercase font-semibold">
              CASE MANAGEMENT
            </div>
            <h2 className="text-lg font-serif text-white mt-0.5">Create Operational Case</h2>
          </div>
          <button
            onClick={onClose}
            className="text-[#777A88] hover:text-white p-1 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 text-xs bg-[#D05B5B]/10 border border-[#D05B5B]/30 rounded text-[#D05B5B]">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-[11px] font-mono text-[#9194A1] uppercase mb-1">
              Case Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Critical Device Reuse Ring Incident #1092"
              className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-2 text-xs text-white placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-mono text-[#9194A1] uppercase mb-1">
                Triage Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as CasePriority)}
                className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#CC9166]"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-[#9194A1] uppercase mb-1">
                Assigned Owner
              </label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="analyst_01"
                className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-2 text-xs text-white placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166]"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-[#9194A1] uppercase mb-1">
              Initial Triage Notes / Hypothesis
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record initial observations, hypothesis, or linked syndicate patterns..."
              className="w-full bg-[#121317] border border-[#1C1D22] rounded px-3 py-2 text-xs text-white placeholder-[#5E616E] focus:outline-none focus:border-[#CC9166]"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#1C1D22]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs text-[#9194A1] hover:text-white rounded border border-[#1C1D22] hover:bg-[#121317] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded bg-[#CC9166] text-[#08080A] hover:bg-[#CC9166]/90 disabled:opacity-40 transition-opacity"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>{loading ? "Creating..." : "Create Case"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
