"use client";

import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight, Shield } from "lucide-react";
import { useAsync } from "@/hooks/use-async";
import { searchRAG } from "@/lib/api";
import type { RAGSearchResponse } from "@/lib/api";

interface RagCitationsCardProps {
  query?: string;
}

export function RagCitationsCard({ query = "syndicate fraud playbooks" }: RagCitationsCardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const ragData = useAsync<RAGSearchResponse>(
    () => searchRAG(query, 3).catch(() => ({ query, results: [], total_results: 0 })),
    [query]
  );

  const results = ragData.status === "success" ? ragData.data.results : [];

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#0A0C10]/95 p-5 space-y-4 shadow-xl backdrop-blur-xl transition-all">
      {/* Header */}
      <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-[#CC9166]/15 flex items-center justify-center text-[#CC9166]">
            <BookOpen className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#CC9166] font-semibold">
              TYPOLOGY REFERENCE
            </div>
            <h3 className="text-sm font-serif text-white">
              Regulatory RAG Citations
            </h3>
          </div>
        </div>
        <span className="text-[9px] font-mono text-[#777A88] bg-[#12141A] px-2 py-0.5 rounded-md border border-white/[0.06]">
          Supporting Intelligence
        </span>
      </div>

      <p className="text-[11px] text-[#9194A1] font-sans leading-relaxed">
        Retrieved regulatory typologies and AML playbooks to benchmark observed multi-entity patterns against compliance baselines.
      </p>

      {ragData.status === "loading" && (
        <div className="py-4 text-center text-xs text-[#777A88]">Retrieving knowledge embeddings...</div>
      )}

      {results.length === 0 && ragData.status === "success" && (
        <div className="py-4 text-center text-xs text-[#777A88]">
          No external typology documents matched query.
        </div>
      )}

      <div className="space-y-2">
        {results.map((doc, idx) => {
          const isExpanded = expandedId === doc.chunk_id || (idx === 0 && expandedId === null);

          return (
            <div
              key={doc.chunk_id || idx}
              className="bg-[#12141A] border border-white/[0.06] hover:border-white/[0.12] rounded-lg overflow-hidden text-xs transition-all"
            >
              <div
                onClick={() => setExpandedId(isExpanded ? "" : doc.chunk_id)}
                className="p-3 flex items-start justify-between gap-2 cursor-pointer select-none"
              >
                <div className="space-y-0.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Shield className="h-3.5 w-3.5 text-[#CC9166] flex-shrink-0" />
                    <span className="font-mono font-semibold text-[#E2E3E9] text-[11px] truncate">
                      {doc.document_title || doc.source_id}
                    </span>
                  </div>
                  <div className="text-[9px] font-mono text-[#777A88]">
                    chunk: {doc.chunk_id} • similarity: {Math.round(doc.similarity * 100)}%
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronDown className="h-3.5 w-3.5 text-[#777A88] mt-0.5 flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 text-[#777A88] mt-0.5 flex-shrink-0" />
                )}
              </div>

              {isExpanded && (
                <div className="px-3 pb-3 pt-2 border-t border-white/[0.06] bg-[#0A0C10] text-[11px] text-[#9194A1] leading-relaxed">
                  <p>{doc.content}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
