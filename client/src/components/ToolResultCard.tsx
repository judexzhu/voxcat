import Markdown from "react-markdown";

interface Props {
  functionName: string;
  result: unknown;
  cancelled: boolean;
}

function resultToMarkdown(functionName: string, result: unknown): string {
  if (typeof result === "string") return result;
  if (result && typeof result === "object") {
    const obj = result as Record<string, unknown>;
    if (obj.analysis) return String(obj.analysis);
    if (obj.report) return String(obj.report);
    if (obj.content) return String(obj.content);
    if (obj.results && Array.isArray(obj.results)) {
      return obj.results
        .map((r: any) => `- **${r.title || r.name || ""}**: ${r.content || r.url || JSON.stringify(r)}`)
        .join("\n");
    }
    if (obj.status) return `**${obj.status}**: ${obj.message || obj.path || obj.title || ""}`;
    if (obj.error) return `**Error**: ${obj.error}`;
  }
  return "```json\n" + JSON.stringify(result, null, 2) + "\n```";
}

export function ToolResultCard({ functionName, result, cancelled }: Props) {
  if (cancelled) {
    return <div className="tool-result cancelled">{functionName} cancelled</div>;
  }

  const md = resultToMarkdown(functionName, result);

  return (
    <div className="tool-result">
      <div className="tool-name">{functionName}</div>
      <div className="tool-content">
        <Markdown>{md}</Markdown>
      </div>
    </div>
  );
}
