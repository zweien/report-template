"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDraftStore } from "@/lib/stores/draft-store";
import { useAuthStore } from "@/lib/stores/auth-store";

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
  } = useDraftStore();
  const [loading, setLoading] = useState(true);

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
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save]);

  if (authLoading || loading || !draft) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#5B6CF0] border-t-transparent" />
      </div>
    );
  }

  const sectionIds = Object.keys(draft.sections);

  return (
    <div className="flex h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-12 items-center justify-between border-b border-white/[0.06] bg-[#141415] px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-[#8B8B93] hover:text-[#E8E8ED]"
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
          <span className="text-xs text-[#8B8B93]">
            {saveStatus === "saving" && "Saving..."}
            {saveStatus === "saved" && "Saved"}
            {saveStatus === "error" && "Save failed"}
            {saveStatus === "idle" && isDirty && "Unsaved changes"}
          </span>
          <button
            onClick={save}
            disabled={!isDirty || saveStatus === "saving"}
            className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-[#8B8B93] hover:bg-white/5 disabled:opacity-50"
          >
            Save
          </button>
          <button
            onClick={exportDocx}
            className="rounded-md bg-[#5B6CF0] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#5B6CF0]/90"
          >
            Export .docx
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 border-r border-white/[0.06] bg-[#141415] p-3 overflow-y-auto">
          <p className="mb-2 text-xs font-medium text-[#8B8B93]">Sections</p>
          <div className="space-y-1">
            {sectionIds.map((id) => (
              <button
                key={id}
                onClick={() => setActiveSection(id)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  activeSection === id
                    ? "bg-[#5B6CF0]/12 text-[#E8E8ED]"
                    : "text-[#8B8B93] hover:bg-white/[0.04] hover:text-[#E8E8ED]"
                }`}
              >
                {id
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase())}
              </button>
            ))}
          </div>

          {/* Context vars */}
          <div className="mt-6 border-t border-white/[0.06] pt-4">
            <p className="mb-2 text-xs font-medium text-[#8B8B93]">Context</p>
            {Object.entries(draft.context).map(([key, value]) => (
              <div key={key} className="mb-2">
                <label className="mb-0.5 block text-xs text-[#8B8B93]">
                  {key}
                </label>
                <input
                  value={value as string}
                  onChange={(e) => updateContext(key, e.target.value)}
                  className="w-full rounded-md border border-white/[0.06] bg-white/[0.03] px-2 py-1.5 text-xs outline-none focus:border-[#5B6CF0]/50"
                />
              </div>
            ))}
          </div>
        </aside>

        {/* Editor area - placeholder for BlockNote */}
        <main className="flex-1 overflow-y-auto bg-[#0F0F10] p-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="mb-4 text-base font-medium">
              {activeSection
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase())}
            </h2>
            <div className="min-h-[400px] rounded-lg border border-white/[0.06] bg-[#141415] p-4">
              <p className="text-sm text-[#8B8B93]">
                BlockNote editor will be integrated here (Task 11)
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
