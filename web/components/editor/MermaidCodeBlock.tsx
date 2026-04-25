"use client";

import { type BlockNoteEditor } from "@blocknote/core";
import { useCallback, useEffect, useState } from "react";
import MermaidPreview from "./MermaidPreview";

interface MermaidCodeBlockProps {
  editor: BlockNoteEditor;
}

export default function MermaidCodeBlock({ editor }: MermaidCodeBlockProps) {
  const [mermaidCode, setMermaidCode] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const updateMermaidCode = useCallback(() => {
    const blocks = editor.document;
    for (const block of blocks) {
      if (block.type === "codeBlock" && (block.props as any)?.language === "mermaid") {
        const text = ((block.content as any[]) || [])
          .map((seg: any) => seg?.text || "")
          .join("");
        setMermaidCode(text || null);
        return;
      }
    }
    setMermaidCode(null);
  }, [editor]);

  useEffect(() => {
    updateMermaidCode();
    const unsub1 = editor.onChange(() => {
      updateMermaidCode();
    });
    const unsub2 = editor.onSelectionChange(() => {
      updateMermaidCode();
    });
    return () => {
      unsub1();
      unsub2();
    };
  }, [editor, updateMermaidCode]);

  if (!mermaidCode) return null;

  return (
    <div className="mt-2 border-t border-neutral-700 pt-2">
      <button
        type="button"
        onClick={() => setShowPreview((p) => !p)}
        className="mb-2 rounded-md bg-neutral-700 px-3 py-1.5 text-xs font-medium text-neutral-200 transition-colors hover:bg-neutral-600"
      >
        {showPreview ? "Show Code" : "Show Diagram"}
      </button>
      {showPreview && <MermaidPreview code={mermaidCode} />}
    </div>
  );
}
