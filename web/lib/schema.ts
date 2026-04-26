import { BlockNoteSchema } from "@blocknote/core";
import { MermaidBlockSpec } from "@/components/editor/MermaidBlock";
import { TableCaptionBlockSpec } from "@/components/editor/TableCaptionBlock";

export const schema = BlockNoteSchema.create().extend({
  blockSpecs: {
    mermaidBlock: MermaidBlockSpec(),
    tableCaption: TableCaptionBlockSpec(),
  },
});
