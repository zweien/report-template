"use client";

import { useCreateBlockNote, SuggestionMenuController, getDefaultReactSlashMenuItems } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import { filterSuggestionItems, insertOrUpdateBlockForSlashMenu } from "@blocknote/core/extensions";
import "@blocknote/shadcn/style.css";
import { useCallback, useEffect, useRef } from "react";
import {
  engineToBlocknoteBlocks,
  type EngineBlock,
} from "@/lib/converter/engine-to-blocknote";
import { schema } from "@/lib/schema";
import api from "@/lib/api";

interface SectionEditorProps {
  blocks: EngineBlock[];
  onChange: (blocks: any[]) => void;
  scrollToBlockId?: string;
  onScrolled?: () => void;
}

function isBlockNoteBlocks(blocks: EngineBlock[]): boolean {
  return blocks.length > 0 && blocks.every(
    (b) => typeof b === "object" && b != null && "id" in b && "type" in b && "children" in b
  );
}

function migrateMermaidBlocks(blocks: any[]): any[] {
  return blocks.map((block) => {
    if (block.type === "codeBlock" && block.props?.language === "mermaid") {
      const content = block.content || [];
      const code = content
        .map((seg: any) => seg?.text || "")
        .join("");
      return {
        id: block.id,
        type: "mermaidBlock",
        props: { code },
        children: block.children || [],
      };
    }
    return block;
  });
}

function prepareBlocks(blocks: EngineBlock[]): any[] {
  if (blocks.length === 0) return [];
  const raw = isBlockNoteBlocks(blocks) ? blocks : engineToBlocknoteBlocks(blocks);
  return migrateMermaidBlocks(raw).filter((b: any) => {
    if (b.type === "image" && !b.props?.url) return false;
    return true;
  });
}

export default function SectionEditor({ blocks, onChange, scrollToBlockId, onScrolled }: SectionEditorProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const editor = useCreateBlockNote({
    schema,
    uploadFile: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/upload/image", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data.url;
    },
  });

  // Load content after mount via replaceBlocks so errors can be caught
  const blocksLoadedRef = useRef(false);
  useEffect(() => {
    if (blocksLoadedRef.current) return;
    blocksLoadedRef.current = true;
    const prepared = prepareBlocks(blocks);
    if (prepared.length > 0) {
      try {
        editor.replaceBlocks(editor.document, prepared);
      } catch {}
    }
  }, [editor]);

  const handleEditorChange = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onChangeRef.current(editor.document);
    }, 100);
  }, [editor]);

  // Scroll to a specific block after editor mounts
  useEffect(() => {
    if (!scrollToBlockId) return;
    const timer = setTimeout(() => {
      const el = document.querySelector(
        `[data-id="${scrollToBlockId}"]`
      ) as HTMLElement | null;
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        try { editor.setTextCursorPosition(scrollToBlockId, "start"); } catch {}
      }
      onScrolled?.();
    }, 150);
    return () => clearTimeout(timer);
  }, [scrollToBlockId, editor, onScrolled]);

  const getSlashMenuItems = useCallback(
    async (query: string) => {
      const defaultItems = getDefaultReactSlashMenuItems(editor);
      const mermaidItem = {
        key: "mermaidBlock" as any,
        title: "Mermaid Diagram",
        subtext: "插入 mermaid 流程图/图表",
        group: "Advanced" as any,
        aliases: ["mermaid", "diagram", "flowchart", "chart"],
        icon: (
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="5" rx="1" />
            <rect x="14" y="16" width="7" height="5" rx="1" />
            <path d="M6.5 8v5.5a2 2 0 0 0 2 2H14" />
            <path d="M14 12l3.5 3.5" />
          </svg>
        ),
        onItemClick: () =>
          insertOrUpdateBlockForSlashMenu(editor, {
            type: "mermaidBlock",
            props: { code: "graph TD\n  A --> B" },
          }),
      };

      // Insert mermaid into the Advanced group, right after the last Advanced item
      const items = [...defaultItems];
      let insertIdx = items.length;
      for (let i = items.length - 1; i >= 0; i--) {
        if ((items[i] as any).group === "Advanced") {
          insertIdx = i + 1;
          break;
        }
      }
      items.splice(insertIdx, 0, mermaidItem);

      return filterSuggestionItems(items, query);
    },
    [editor],
  );

  return (
    <div className="min-h-[400px]">
      <BlockNoteView
        editor={editor}
        onChange={handleEditorChange}
        theme="dark"
        slashMenu={false}
        sideMenu
        formattingToolbar
      >
        <SuggestionMenuController
          triggerCharacter="/"
          getItems={getSlashMenuItems}
        />
      </BlockNoteView>
    </div>
  );
}
