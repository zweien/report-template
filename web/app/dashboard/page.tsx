"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";
import api from "@/lib/api";

interface Template {
  id: string;
  name: string;
  parsed_structure: { sections: { id: string; title: string }[] };
  created_at: string;
}

interface Draft {
  id: string;
  template_id: string;
  title: string;
  status: string;
  updated_at: string;
}

export default function DashboardPage() {
  const { user, isLoading, checkAuth, logout } = useAuthStore();
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (user) {
      Promise.all([api.get("/templates"), api.get("/drafts")]).then(([t, d]) => {
        setTemplates(t.data);
        setDrafts(d.data);
        setLoading(false);
      });
    }
  }, [user]);

  const handleNewDraft = async (templateId: string) => {
    const { data } = await api.post("/drafts", {
      template_id: templateId,
      title: "Untitled",
    });
    router.push(`/drafts/${data.id}`);
  };

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm("Delete this template?")) return;
    await api.delete(`/templates/${id}`);
    setTemplates((prev) => prev.filter((t) => t.id !== id));
  };

  const handleDeleteDraft = async (id: string) => {
    if (!confirm("Delete this draft?")) return;
    await api.delete(`/drafts/${id}`);
    setDrafts((prev) => prev.filter((d) => d.id !== id));
  };

  if (isLoading || !user) return null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Report Editor</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[var(--text-secondary)]">{user.username}</span>
          <button
            onClick={logout}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            Sign out
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-lg bg-[var(--surface-transparent-hover)]"
            />
          ))}
        </div>
      ) : (
        <>
          <section className="mb-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-[var(--text-secondary)]">
                Templates
              </h2>
              <Link
                href="/dashboard/templates/upload"
                className="rounded-md bg-[var(--brand)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--brand)]/90"
              >
                Upload
              </Link>
            </div>
            {templates.length === 0 ? (
              <p className="text-sm text-[var(--text-secondary)]">
                No templates yet. Upload a .docx to get started.
              </p>
            ) : (
              <div className="space-y-2">
                {templates.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-panel)] px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{t.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">
                        {t.parsed_structure.sections.length} sections
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleNewDraft(t.id)}
                        className="rounded-md bg-[var(--brand-10)] px-3 py-1.5 text-xs font-medium text-[var(--brand)] hover:bg-[var(--brand-20)]"
                      >
                        New Draft
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(t.id)}
                        className="rounded-md px-2 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-transparent-hover)] hover:text-red-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-[var(--text-secondary)]">
              Drafts
            </h2>
            {drafts.length === 0 ? (
              <p className="text-sm text-[var(--text-secondary)]">No drafts yet.</p>
            ) : (
              <div className="space-y-2">
                {drafts.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-panel)] px-4 py-3"
                  >
                    <Link href={`/drafts/${d.id}`} className="flex-1">
                      <p className="text-sm font-medium hover:text-[var(--brand)]">
                        {d.title}
                      </p>
                      <p className="text-xs text-[var(--text-secondary)]">
                        Updated{" "}
                        {new Date(d.updated_at).toLocaleString()}
                      </p>
                    </Link>
                    <button
                      onClick={() => handleDeleteDraft(d.id)}
                      className="rounded-md px-2 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-transparent-hover)] hover:text-red-400"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
