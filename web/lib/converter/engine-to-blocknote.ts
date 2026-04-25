/**
 * report-engine → BlockNote converter
 *
 * Converts report-engine payload blocks into BlockNote editor blocks
 * for display in the editor.
 */

export interface EngineBlock {
  type: string;
  [key: string]: any;
}

export interface BlockNoteBlock {
  id: string;
  type: string;
  props?: Record<string, any>;
  content?: any;
}

let blockIdCounter = 0;

function nextId(): string {
  return `bn-${++blockIdCounter}`;
}

/**
 * Convert an array of report-engine blocks into BlockNote blocks.
 */
export function engineToBlocknoteBlocks(
  blocks: EngineBlock[]
): BlockNoteBlock[] {
  const result: BlockNoteBlock[] = [];

  for (const block of blocks) {
    switch (block.type) {
      case "heading":
        result.push({
          id: nextId(),
          type: "heading",
          props: { level: block.level || 2 },
          content: [{ type: "text", text: block.text || "" }],
        });
        break;

      case "paragraph":
        result.push({
          id: nextId(),
          type: "paragraph",
          content: [{ type: "text", text: block.text || "" }],
        });
        break;

      case "rich_paragraph":
        result.push({
          id: nextId(),
          type: "paragraph",
          content: (block.segments || []).map((seg: any) => ({
            type: "text",
            text: seg.text || "",
            styles: {
              ...(seg.bold ? { bold: true } : {}),
              ...(seg.italic ? { italic: true } : {}),
            },
          })),
        });
        break;

      case "bullet_list":
        for (const item of block.items || []) {
          result.push({
            id: nextId(),
            type: "bulletListItem",
            content: [{ type: "text", text: item }],
          });
        }
        break;

      case "numbered_list":
        for (const item of block.items || []) {
          result.push({
            id: nextId(),
            type: "numberedListItem",
            content: [{ type: "text", text: item }],
          });
        }
        break;

      case "table":
        // BlockNote tables have a different structure; store as-is for now
        // and let the editor re-create from the engine format
        result.push({
          id: nextId(),
          type: "table",
          content: buildTableContent(block.headers || [], block.rows || []),
        });
        break;

      case "quote":
        result.push({
          id: nextId(),
          type: "quote",
          content: [{ type: "text", text: block.text || "" }],
        });
        break;

      case "code_block":
        result.push({
          id: nextId(),
          type: "codeBlock",
          content: [{ type: "text", text: block.code || "" }],
        });
        break;

      case "page_break":
        result.push({
          id: nextId(),
          type: "pageBreak",
        });
        break;

      // Blocks not supported by BlockNote are silently skipped
      default:
        break;
    }
  }

  return result;
}

/**
 * Build BlockNote table content from headers + rows.
 */
function buildTableContent(
  headers: string[],
  rows: string[][]
): any[][] {
  const headerRow = headers.map((h) => ({ content: [{ type: "text", text: h }] }));
  const dataRows = rows.map((row) =>
    row.map((cell) => ({ content: [{ type: "text", text: cell }] }))
  );
  return [headerRow, ...dataRows];
}
