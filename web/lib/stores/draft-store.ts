import { create } from "zustand";
import api from "@/lib/api";

interface DraftData {
  id: string;
  template_id: string;
  title: string;
  context: Record<string, string>;
  sections: Record<string, any[]>;
  attachments: Record<string, any[]>;
  status: string;
}

interface DraftStore {
  draft: DraftData | null;
  activeSection: string;
  isDirty: boolean;
  saveStatus: "idle" | "saving" | "saved" | "error";

  loadDraft: (id: string) => Promise<void>;
  setActiveSection: (id: string) => void;
  updateSection: (id: string, blocks: any[]) => void;
  updateContext: (key: string, value: string) => void;
  updateTitle: (title: string) => void;
  save: () => Promise<void>;
  exportDocx: () => Promise<void>;
}

export const useDraftStore = create<DraftStore>((set, get) => ({
  draft: null,
  activeSection: "",
  isDirty: false,
  saveStatus: "idle",

  loadDraft: async (id) => {
    const { data } = await api.get(`/drafts/${id}`);
    const sectionIds = Object.keys(data.sections);
    set({
      draft: data,
      activeSection: sectionIds[0] || "",
      isDirty: false,
      saveStatus: "idle",
    });
  },

  setActiveSection: (id) => set({ activeSection: id }),

  updateSection: (id, blocks) => {
    const { draft } = get();
    if (!draft) return;
    set({
      draft: { ...draft, sections: { ...draft.sections, [id]: blocks } },
      isDirty: true,
      saveStatus: "idle",
    });
  },

  updateContext: (key, value) => {
    const { draft } = get();
    if (!draft) return;
    set({
      draft: { ...draft, context: { ...draft.context, [key]: value } },
      isDirty: true,
      saveStatus: "idle",
    });
  },

  updateTitle: (title) => {
    const { draft } = get();
    if (!draft) return;
    set({ draft: { ...draft, title }, isDirty: true, saveStatus: "idle" });
  },

  save: async () => {
    const { draft } = get();
    if (!draft) return;
    set({ saveStatus: "saving" });
    try {
      await api.patch(`/drafts/${draft.id}`, {
        title: draft.title,
        context: draft.context,
        sections: draft.sections,
        attachments: draft.attachments,
      });
      set({ isDirty: false, saveStatus: "saved" });
    } catch {
      set({ saveStatus: "error" });
    }
  },

  exportDocx: async () => {
    const { draft, save } = get();
    if (!draft) return;
    await save();
    const response = await api.post(`/drafts/${draft.id}/export`, null, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${draft.title}.docx`;
    a.click();
    window.URL.revokeObjectURL(url);
  },
}));
