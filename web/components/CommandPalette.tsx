"use client";

import { useEffect, useState, useRef } from "react";

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  commands: Command[];
  open: boolean;
  onClose: () => void;
}

export default function CommandPalette({ commands, open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg border border-white/[0.06] bg-[#141415] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a command..."
          className="w-full border-b border-white/[0.06] bg-transparent px-4 py-3 text-sm outline-none"
        />
        <div className="max-h-64 overflow-y-auto p-1">
          {filtered.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => { cmd.action(); onClose(); }}
              className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm text-[#E8E8ED] hover:bg-[#5B6CF0]/12"
            >
              <span>{cmd.label}</span>
              {cmd.shortcut && <span className="text-xs text-[#8B8B93]">{cmd.shortcut}</span>}
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="px-3 py-2 text-sm text-[#8B8B93]">No commands found</p>
          )}
        </div>
      </div>
    </div>
  );
}
