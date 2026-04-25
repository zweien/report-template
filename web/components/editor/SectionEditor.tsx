"use client";

import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { useCallback, useRef } from "react";
import {
  blocknoteToEngineBlocks,
  type BlockNoteBlock,
} from "@/lib/converter/blocknote-to-engine";
import {
  engineToBlocknoteBlocks,
  type EngineBlock,
} from "@/lib/converter/engine-to-blocknote";

interface SectionEditorProps {
  /** Engine blocks to display (converted to BlockNote format on mount). */
  blocks: EngineBlock[];
  /** Called when the user edits; receives engine-format blocks. */
  onChange: (blocks: EngineBlock[]) => void;
}

/**
 * Rich-text editor for a single draft section.
 *
 * Converts between engine blocks (storage) and BlockNote blocks (editor)
 * and debounces onChange callbacks to avoid excessive re-renders.
 */
export default function SectionEditor({ blocks, onChange }: SectionEditorProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Convert engine blocks to BlockNote format for initial content
  const initialContent =
    blocks.length > 0 ? engineToBlocknoteBlocks(blocks) : undefined;

  const editor = useCreateBlockNote({ initialContent });

  const handleEditorChange = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const engineBlocks = blocknoteToEngineBlocks(
        editor.document as BlockNoteBlock[]
      );
      onChangeRef.current(engineBlocks);
    }, 100);
  }, [editor]);

  return (
    <div className="min-h-[400px]">
      <BlockNoteView
        editor={editor}
        onChange={handleEditorChange}
        theme="dark"
      />
    </div>
  );
}
