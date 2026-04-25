"use client";

import { createReactBlockSpec, type ReactCustomBlockRenderProps } from "@blocknote/react";
import { useCallback, useEffect, useRef, useState } from "react";
import MermaidPreview from "./MermaidPreview";

function MermaidBlockRender({ block, editor }: ReactCustomBlockRenderProps<any>) {
  const [mode, setMode] = useState<"code" | "preview">("code");
  const [localCode, setLocalCode] = useState(block.props.code || "");
  const [hovered, setHovered] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const newCode = block.props.code || "";
    if (newCode !== localCode) {
      setLocalCode(newCode);
    }
  }, [block.props.code]);

  const persistCode = useCallback(
    (code: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        editor.updateBlock(block.id, {
          type: "mermaidBlock",
          props: { code },
        });
      }, 300);
    },
    [editor, block.id],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const val = e.target.value;
      setLocalCode(val);
      persistCode(val);
    },
    [persistCode],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const ta = e.currentTarget;
        const start = ta.selectionStart;
        const end = ta.selectionEnd;
        const val = ta.value;
        const next = val.substring(0, start) + "  " + val.substring(end);
        setLocalCode(next);
        persistCode(next);
        requestAnimationFrame(() => {
          ta.selectionStart = ta.selectionEnd = start + 2;
        });
      }
    },
    [persistCode],
  );

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div
      className="my-2 rounded-lg border border-neutral-700 bg-neutral-900"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Hover toolbar */}
      <div className="flex items-center justify-between border-b border-neutral-700 px-3 py-1.5">
        <span className="text-xs font-medium text-neutral-400">Mermaid</span>
        <div
          className={`flex gap-1 transition-opacity ${hovered || mode === "preview" ? "opacity-100" : "opacity-0"}`}
        >
          <button
            type="button"
            onClick={() => setMode("code")}
            className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
              mode === "code"
                ? "bg-blue-600 text-white"
                : "bg-neutral-700 text-neutral-300 hover:bg-neutral-600"
            }`}
          >
            代码
          </button>
          <button
            type="button"
            onClick={() => setMode("preview")}
            className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
              mode === "preview"
                ? "bg-blue-600 text-white"
                : "bg-neutral-700 text-neutral-300 hover:bg-neutral-600"
            }`}
          >
            预览
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-3">
        {mode === "code" ? (
          <textarea
            ref={textareaRef}
            value={localCode}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="graph TD&#10;  A --> B"
            className="min-h-[120px] w-full resize-y rounded border border-neutral-700 bg-neutral-950 p-3 font-mono text-sm text-neutral-200 placeholder-neutral-500 focus:border-blue-500 focus:outline-none"
            rows={Math.max(5, localCode.split("\n").length + 1)}
          />
        ) : (
          <MermaidPreview code={localCode} />
        )}
      </div>
    </div>
  );
}

export const MermaidBlockSpec = createReactBlockSpec(
  {
    type: "mermaidBlock" as const,
    propSchema: {
      code: { default: "graph TD\n  A --> B" },
    },
    content: "none" as const,
  },
  {
    render: MermaidBlockRender,
    toExternalHTML: (props: any) => (
      <pre>
        <code className="language-mermaid">{props.block.props.code || ""}</code>
      </pre>
    ),
    parse: (el: HTMLElement) => {
      const codeEl =
        el.tagName === "CODE" ? el : el.querySelector("code");
      if (codeEl) {
        const classes = codeEl.getAttribute("class") || "";
        if (classes.includes("mermaid")) {
          return { code: codeEl.textContent || "" };
        }
      }
      return undefined;
    },
  },
);
