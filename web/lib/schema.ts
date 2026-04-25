import { BlockNoteSchema, createCodeBlockSpec } from "@blocknote/core";

export const schema = BlockNoteSchema.create().extend({
  blockSpecs: {
    codeBlock: createCodeBlockSpec({
      supportedLanguages: {
        mermaid: { name: "Mermaid" },
      },
    }),
  },
});
