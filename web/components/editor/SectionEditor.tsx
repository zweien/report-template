"use client";

import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { useCallback, useRef } from "react";
import {
  engineToBlocknoteBlocks,
  type EngineBlock,
} from "@/lib/converter/engine-to-blocknote";
import { schema } from "@/lib/schema";
import api from "@/lib/api";
import MermaidCodeBlock from "./MermaidCodeBlock";

interface SectionEditorProps {
  /** Blocks to display. Can be engine-format or already BlockNote-format. */
  blocks: EngineBlock[];
  /** Called when the user edits; receives the updated blocks. */
  onChange: (blocks: any[]) => void;
}

function isBlockNoteBlocks(blocks: EngineBlock[]): boolean {
  return blocks.length > 0 && blocks.every(
    (b) => typeof b === "object" && b != null && "id" in b && "type" in b && "children" in b
  );
}

export default function SectionEditor({ blocks, onChange }: SectionEditorProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // If blocks are already in BlockNote format (stored from editor), use directly.
  // Otherwise convert from engine format.
  const initialContent = blocks.length > 0
    ? isBlockNoteBlocks(blocks)
      ? blocks
      : engineToBlocknoteBlocks(blocks)
    : undefined;

  const editor = useCreateBlockNote({
    schema,
    initialContent,
    uploadFile: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/upload/image", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data.url;
    },
  });

  const handleEditorChange = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onChangeRef.current(editor.document);
    }, 100);
  }, [editor]);

  return (
    <div className="min-h-[400px]">
      <BlockNoteView
        editor={editor}
        onChange={handleEditorChange}
        theme="dark"
        slashMenu
        sideMenu
        formattingToolbar
      />
      <MermaidCodeBlock editor={editor} />
    </div>
  );
}
