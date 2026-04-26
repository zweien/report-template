"use client";

import { useMemo } from "react";

interface HeadingItem {
  id: string;
  text: string;
  level: number;
  sectionId: string;
}

interface OutlinePanelProps {
  sections: Record<string, any[]>;
  sectionEnabled: Record<string, boolean>;
  activeSection: string;
  onNavigateHeading: (sectionId: string, blockId: string) => void;
}

function extractHeadings(
  sections: Record<string, any[]>,
  sectionEnabled: Record<string, boolean>
): HeadingItem[] {
  const headings: HeadingItem[] = [];
  for (const [sectionId, blocks] of Object.entries(sections)) {
    if (sectionEnabled[sectionId] === false) continue;
    if (!Array.isArray(blocks)) continue;
    for (const block of blocks) {
      if (block.type === "heading" && block.id) {
        const text = Array.isArray(block.content)
          ? block.content
              .map((s: any) => (typeof s === "object" ? s.text || "" : ""))
              .join("")
          : "";
        headings.push({
          id: block.id,
          text,
          level: block.props?.level || 2,
          sectionId,
        });
      }
    }
  }
  return headings;
}

export default function OutlinePanel({
  sections,
  sectionEnabled,
  activeSection,
  onNavigateHeading,
}: OutlinePanelProps) {
  const headings = useMemo(
    () => extractHeadings(sections, sectionEnabled),
    [sections, sectionEnabled]
  );

  if (headings.length === 0) {
    return (
      <aside className="w-64 border-l border-[var(--border-subtle)] bg-[var(--bg-panel)] p-3 overflow-y-auto">
        <p className="text-xs text-[var(--text-secondary)]">No headings found</p>
      </aside>
    );
  }

  return (
    <aside className="w-64 border-l border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-y-auto flex flex-col">
      <div className="px-3 pt-3 pb-2">
        <p className="text-xs font-medium text-[var(--text-secondary)]">Outline</p>
      </div>
      <div className="flex-1 px-1 pb-3">
        {headings.map((h) => {
          const isActive = h.sectionId === activeSection;
          const indent = Math.max(0, h.level - 1) * 12;
          return (
            <button
              key={`${h.sectionId}-${h.id}`}
              onClick={() => onNavigateHeading(h.sectionId, h.id)}
              className={`block w-full text-left px-2 py-1 rounded text-xs truncate transition-colors ${
                isActive
                  ? "text-[var(--text-primary)] hover:bg-[var(--surface-transparent)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--surface-transparent)] hover:text-[var(--text-primary)]"
              }`}
              style={{ paddingLeft: `${8 + indent}px` }}
              title={h.text}
            >
              {h.text || "(untitled)"}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
