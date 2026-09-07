"use client";

import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";
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
    <div className="bg-[#040406] border border-[#1C1D22] rounded-lg p-4 space-y-3 shadow-xl">
      <div className="border-b border-[#1C1D22] pb-2.5 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#CC9166] font-semibold">
            REGULATORY & AML KNOWLEDGE
          </div>
          <h3 className="text-sm font-serif text-white font-normal mt-0.5">
            Typology RAG Citations
          </h3>
        </div>
        <span className="text-[9px] font-mono text-[#5E616E]">Vector Grounded</span>
      </div>

      <p className="text-[11px] text-[#9194A1] font-sans">
        External regulatory playbooks and typologies retrieved to benchmark observed behavior against
        compliance baselines.
      </p>

      {ragData.status === "loading" && (
        <div className="py-4 text-center text-xs text-[#777A88]">Searching knowledge base...</div>
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
              className="bg-[#0D0E12] border border-[#1C1D22] rounded-md overflow-hidden text-xs"
            >
              <div
                onClick={() => setExpandedId(isExpanded ? "" : doc.chunk_id)}
                className="p-3 flex items-start justify-between gap-2 cursor-pointer select-none"
              >
                <div className="space-y-0.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-3.5 w-3.5 text-[#CC9166] flex-shrink-0" />
                    <span className="font-mono font-semibold text-[#E2E3E9] text-[11px] truncate">
                      {doc.document_title || doc.source_id}
                    </span>
                  </div>
                  <div className="text-[9px] font-mono text-[#777A88]">
                    chunk: {doc.chunk_id} • sim: {Math.round(doc.similarity * 100)}%
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronDown className="h-3.5 w-3.5 text-[#777A88] mt-0.5" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 text-[#777A88] mt-0.5" />
                )}
              </div>

              {isExpanded && (
                <div className="px-3 pb-3 pt-1 border-t border-[#1C1D22] bg-[#08080A]/60 text-[11px] text-[#9194A1] leading-relaxed">
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
