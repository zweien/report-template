import { BlockNoteSchema } from "@blocknote/core";
import { MermaidBlockSpec } from "@/components/editor/MermaidBlock";

export const schema = BlockNoteSchema.create().extend({
  blockSpecs: {
    mermaidBlock: MermaidBlockSpec(),
  },
});
