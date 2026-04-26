"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDraftStore } from "@/lib/stores/draft-store";
import { useAuthStore } from "@/lib/stores/auth-store";
import SectionEditor from "@/components/editor/SectionEditor";
import type { Payload } from "@/lib/stores/draft-store";
import OutlinePanel from "@/components/editor/OutlinePanel";
import CommandPalette from "@/components/CommandPalette";
import ThemeToggle from "@/components/ThemeToggle";

export default function EditorPage() {
  const params = useParams();
  const router = useRouter();
  const draftId = params.id as string;
  const { user, checkAuth, isLoading: authLoading } = useAuthStore();
  const {
    draft,
    activeSection,
    isDirty,
    saveStatus,
    loadDraft,
    setActiveSection,
    save,
    exportDocx,
    updateTitle,
    updateContext,
    toggleSection,
    importPayload,
  } = useDraftStore();
  const [loading, setLoading] = useState(true);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [outlineOpen, setOutlineOpen] = useState(true);
  const [scrollTargetBlockId, setScrollTargetBlockId] = useState<string | null>(null);

  // Auto-save: debounce 3 seconds after last edit
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleAutoSave = useCallback(() => {
    if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    autoSaveTimerRef.current = setTimeout(() => {
      const { isDirty, save: doSave } = useDraftStore.getState();
      if (isDirty) doSave();
    }, 3000);
  }, []);

  // Cleanup auto-save timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    };
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);

  useEffect(() => {
    if (user) {
      loadDraft(draftId)
        .catch(() => router.push("/dashboard"))
        .finally(() => setLoading(false));
    }
  }, [user, draftId, loadDraft, router]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        save();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save]);

  const handleNavigateHeading = useCallback(
    (sectionId: string, blockId: string) => {
      if (sectionId !== activeSection) {
        setActiveSection(sectionId);
      }
      setScrollTargetBlockId(blockId);
    },
    [activeSection, setActiveSection]
  );

  const handleScrolled = useCallback(() => {
    setScrollTargetBlockId(null);
  }, []);

  const importInputRef = useRef<HTMLInputElement>(null);
  const handleImportPayload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const payload: Payload = JSON.parse(reader.result as string);
          importPayload(payload);
          scheduleAutoSave();
        } catch {
          alert("Invalid JSON file");
        }
      };
      reader.readAsText(file);
      e.target.value = "";
    },
    [importPayload, scheduleAutoSave]
  );

  if (authLoading || loading || !draft) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--brand)] border-t-transparent" />
      </div>
    );
  }

  const sectionIds = Object.keys(draft.sections);

  const commands = [
    { id: "save", label: "Save", shortcut: "⌘S", action: save },
    { id: "export", label: "Export .docx", shortcut: "⌘⇧E", action: exportDocx },
    ...sectionIds.map((id) => ({
      id: `section-${id}`,
      label: `Go to: ${id.replace(/_/g, " ")}`,
      action: () => setActiveSection(id),
    })),
  ];

  return (
    <div className="flex h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-12 items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-panel)] px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            ← Back
          </button>
          <input
            value={draft.title}
            onChange={(e) => updateTitle(e.target.value)}
            className="bg-transparent text-sm font-medium outline-none"
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--text-secondary)]">
            {saveStatus === "saving" && "Saving..."}
            {saveStatus === "saved" && "Saved"}
            {saveStatus === "error" && "Save failed"}
            {saveStatus === "idle" && isDirty && "Unsaved changes"}
          </span>
          <input
            ref={importInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleImportPayload}
          />
          <button
            onClick={() => importInputRef.current?.click()}
            className="rounded-md border border-[var(--border-standard)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-transparent-hover)]"
          >
            Import
          </button>
          <button
            onClick={save}
            disabled={!isDirty || saveStatus === "saving"}
            className="rounded-md border border-[var(--border-standard)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-transparent-hover)] disabled:opacity-50"
          >
            Save
          </button>
          <button
            onClick={exportDocx}
            className="rounded-md bg-[var(--brand)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--brand)]/90"
          >
            Export .docx
          </button>
          <ThemeToggle />
          <button
            onClick={() => setOutlineOpen((v) => !v)}
            className={`rounded-md border px-2.5 py-1.5 text-xs transition-colors ${
              outlineOpen
                ? "border-[var(--brand)]/40 text-[var(--brand)]"
                : "border-[var(--border-standard)] text-[var(--text-secondary)] hover:bg-[var(--surface-transparent-hover)]"
            }`}
            title={outlineOpen ? "Hide outline" : "Show outline"}
          >
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 border-r border-[var(--border-subtle)] bg-[var(--bg-panel)] p-3 overflow-y-auto">
          <p className="mb-2 text-xs font-medium text-[var(--text-secondary)]">Sections</p>
          <div className="space-y-1">
            {sectionIds.map((id) => {
              const enabled = draft.section_enabled?.[id] !== false;
              return (
                <div
                  key={id}
                  className={`group flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors ${
                    activeSection === id
                      ? "bg-[var(--brand-10)] text-[var(--text-primary)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-transparent)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  <button
                    onClick={() => setActiveSection(id)}
                    className="flex-1 text-left text-sm"
                  >
                    {id
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleSection(id); scheduleAutoSave(); }}
                    className={`flex-shrink-0 h-4 w-7 rounded-full transition-colors ${
                      enabled ? "bg-[var(--brand)]" : "bg-[var(--surface-transparent-hover)]"
                    }`}
                    title={enabled ? "Disable section" : "Enable section"}
                  >
                    <span
                      className={`block h-3 w-3 rounded-full bg-white transition-transform ${
                        enabled ? "translate-x-3.5" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Context vars */}
          <div className="mt-6 border-t border-[var(--border-subtle)] pt-4">
            <p className="mb-2 text-xs font-medium text-[var(--text-secondary)]">Context</p>
            {Object.entries(draft.context).map(([key, value]) => (
              <div key={key} className="mb-2">
                <label className="mb-0.5 block text-xs text-[var(--text-secondary)]">
                  {key}
                </label>
                <input
                  value={value as string}
                  onChange={(e) => updateContext(key, e.target.value)}
                  className="w-full rounded-md border border-[var(--border-subtle)] bg-[var(--surface-transparent)] px-2 py-1.5 text-xs outline-none focus:border-[var(--brand)]/50"
                />
              </div>
            ))}
          </div>
        </aside>

        {/* Editor area - placeholder for BlockNote */}
        <main className="flex-1 overflow-y-auto bg-[var(--bg-canvas)] p-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="mb-4 text-base font-medium">
              {activeSection
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase())}
            </h2>
            {draft.section_enabled?.[activeSection] === false ? (
              <div className="flex flex-col items-center justify-center py-16 text-[var(--text-secondary)]">
                <p className="text-sm">This section is disabled and will not appear in exports.</p>
                <button
                  onClick={() => { toggleSection(activeSection); scheduleAutoSave(); }}
                  className="mt-3 rounded-md bg-[var(--brand)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--brand)]/90"
                >
                  Enable section
                </button>
              </div>
            ) : (
              <SectionEditor
                key={activeSection}
                blocks={draft.sections[activeSection] || []}
                onChange={(blocks) => {
                  useDraftStore.getState().updateSection(activeSection, blocks);
                  scheduleAutoSave();
                }}
                scrollToBlockId={scrollTargetBlockId ?? undefined}
                onScrolled={handleScrolled}
              />
            )}
          </div>
        </main>

        {/* Outline panel */}
        {outlineOpen && (
          <OutlinePanel
            sections={draft.sections}
            sectionEnabled={draft.section_enabled}
            activeSection={activeSection}
            onNavigateHeading={handleNavigateHeading}
          />
        )}
      </div>

      <CommandPalette commands={commands} open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
