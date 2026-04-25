/**
 * BlockNote → report-engine converter
 *
 * Converts BlockNote editor blocks into report-engine payload blocks
 * suitable for storage and .docx export.
 */

export interface BlockNoteBlock {
  id: string;
  type: string;
  props?: Record<string, any>;
  content?: any;
  children?: BlockNoteBlock[];
}

export interface EngineBlock {
  type: string;
  [key: string]: any;
}

/**
 * Extract plain text from BlockNote inline content.
 */
function extractText(content: any): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((seg: any) => seg?.text || "")
      .join("");
  }
  return "";
}

/**
 * Check if inline content has any non-trivial styles.
 */
function hasInlineStyles(segments: any[]): boolean {
  return (
    Array.isArray(segments) &&
    segments.some(
      (seg: any) => seg?.styles && Object.keys(seg.styles).length > 0
    )
  );
}

/**
 * Convert a single BlockNote block to a report-engine block.
 */
function convertBlock(block: BlockNoteBlock): EngineBlock | null {
  const type = block.type;

  switch (type) {
    case "heading": {
      const level = block.props?.level || 2;
      return { type: "heading", text: extractText(block.content), level };
    }

    case "paragraph": {
      if (hasInlineStyles(block.content)) {
        const segments = (block.content || []).map((seg: any) => {
          const s: any = { text: seg.text || "" };
          if (seg.styles?.bold) s.bold = true;
          if (seg.styles?.italic) s.italic = true;
          return s;
        });
        return { type: "rich_paragraph", segments };
      }
      return { type: "paragraph", text: extractText(block.content) };
    }

    case "bulletListItem":
      return { type: "bullet_list", items: [extractText(block.content)] };

    case "numberedListItem":
      return { type: "numbered_list", items: [extractText(block.content)] };

    case "table": {
      const content = block.content;
      if (!Array.isArray(content) || content.length === 0) return null;
      const headers =
        content[0]?.map?.((c: any) => extractText(c?.content || c)) || [];
      const dataRows =
        content
          .slice(1)
          ?.map((r: any) =>
            r.map?.((c: any) => extractText(c?.content || c)) || []
          ) || [];
      return { type: "table", title: "", headers, rows: dataRows };
    }

    case "quote":
      return { type: "quote", text: extractText(block.content) };

    case "codeBlock":
      return { type: "code_block", code: extractText(block.content) };

    case "image":
      return {
        type: "image",
        path: block.props?.url || block.props?.src || "",
        width: block.props?.width,
        caption: block.props?.caption || "",
      };

    case "pageBreak":
      return { type: "page_break" };

    default:
      return null;
  }
}

/**
 * Convert an array of BlockNote blocks into report-engine blocks.
 * Consecutive list items are merged into a single list block.
 */
export function blocknoteToEngineBlocks(
  blocks: BlockNoteBlock[]
): EngineBlock[] {
  const result: EngineBlock[] = [];
  let i = 0;

  while (i < blocks.length) {
    const block = blocks[i];

    // Merge consecutive bullet list items
    if (block.type === "bulletListItem") {
      const items: string[] = [];
      while (i < blocks.length && blocks[i].type === "bulletListItem") {
        items.push(extractText(blocks[i].content));
        i++;
      }
      result.push({ type: "bullet_list", items });
      continue;
    }

    // Merge consecutive numbered list items
    if (block.type === "numberedListItem") {
      const items: string[] = [];
      while (i < blocks.length && blocks[i].type === "numberedListItem") {
        items.push(extractText(blocks[i].content));
        i++;
      }
      result.push({ type: "numbered_list", items });
      continue;
    }

    const converted = convertBlock(block);
    if (converted) result.push(converted);
    i++;
  }

  return result;
}
