import { create } from "zustand";
import api from "@/lib/api";
import { payloadToDraftSections } from "@/lib/converter/engine-to-blocknote";

interface DraftData {
  id: string;
  template_id: string;
  title: string;
  context: Record<string, string>;
  sections: Record<string, any[]>;
  attachments: Record<string, any[]>;
  section_enabled: Record<string, boolean>;
  status: string;
}

export interface PayloadSection {
  id: string;
  blocks: any[];
  enabled?: boolean;
  [key: string]: any;
}

export interface Payload {
  context?: Record<string, string>;
  sections?: PayloadSection[];
  [key: string]: any;
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
  toggleSection: (id: string) => void;
  save: () => Promise<void>;
  exportDocx: () => Promise<void>;
  importPayload: (payload: Payload) => void;
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

  toggleSection: (id) => {
    const { draft } = get();
    if (!draft) return;
    const section_enabled = { ...draft.section_enabled, [id]: !draft.section_enabled[id] };
    set({ draft: { ...draft, section_enabled }, isDirty: true, saveStatus: "idle" });
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
        section_enabled: draft.section_enabled,
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

  importPayload: (payload: Payload) => {
    const { draft } = get();
    if (!draft) return;

    const newSections = payloadToDraftSections(
      payload,
      draft.sections,
      draft.section_enabled
    );

    const newContext: Record<string, string> = { ...draft.context };
    if (payload.context) {
      for (const [key, value] of Object.entries(payload.context)) {
        if (key in newContext) {
          newContext[key] = value;
        }
      }
    }

    const newSectionEnabled = { ...draft.section_enabled };
    if (payload.sections) {
      for (const sec of payload.sections) {
        if (sec.id in newSectionEnabled && sec.enabled !== undefined) {
          newSectionEnabled[sec.id] = sec.enabled;
        }
      }
    }

    set({
      draft: {
        ...draft,
        sections: newSections,
        context: newContext,
        section_enabled: newSectionEnabled,
      },
      isDirty: true,
      saveStatus: "idle",
    });
  },
}));
