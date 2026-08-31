import Markdown from "react-markdown";

interface Props {
  functionName: string;
  result: unknown;
  cancelled: boolean;
  latencyMs?: number;
  onFileClick?: (filename: string) => void;
}

type ResultKind = "results" | "prose" | "status" | "raw";

function tryParseJson(val: unknown): unknown {
  if (typeof val === "string" && val.trimStart().startsWith("{")) {
    try { return JSON.parse(val); } catch { /* not JSON */ }
  }
  return val;
}

function classify(result: unknown, cancelled: boolean): ResultKind {
  if (cancelled) return "status";
  const parsed = tryParseJson(result);
  if (parsed && typeof parsed === "object") {
    const obj = parsed as Record<string, unknown>;
    if (obj.error) return "status";
    if (Array.isArray(obj.results)) return "results";
    if (Array.isArray(obj.files)) return "results";
    if (Array.isArray(obj.issues)) return "results";
    if (obj.analysis || obj.report || obj.content) return "prose";
    const keys = Object.keys(obj);
    if (obj.status && keys.length <= 2) return "status";
  }
  if (typeof parsed === "string") return "prose";
  return "raw";
}

function formatLatency(ms?: number): string {
  if (!ms) return "";
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function ResultsList({
  result,
  onFileClick,
}: {
  result: Record<string, unknown>;
  onFileClick?: (filename: string) => void;
}) {
  const items = (result.results || result.files || result.issues) as Array<Record<string, unknown>>;
  const isFiles = Array.isArray(result.files);

  return (
    <div className="tool-result-body">
      {items.map((r, i) => (
        <div key={i} className="tool-result-item">
          <div
            className={`tool-result-title ${isFiles && onFileClick ? "tool-subject-link" : ""}`}
            onClick={isFiles && onFileClick ? () => onFileClick(String(r.name)) : undefined}
          >
            {String(r.title || r.key || r.name || "")}
            {r.key && r.summary ? ` — ${String(r.summary)}` : ""}
          </div>
          {!isFiles && !r.key && r.content != null && (
            <div className="tool-result-snippet">
              {String(r.content).slice(0, 200)}
            </div>
          )}
          {r.status != null && (
            <div className="tool-result-source">{String(r.status)}{r.priority ? ` · ${String(r.priority)}` : ""}</div>
          )}
          {r.url != null && (
            <a
              className="tool-result-source"
              href={String(r.url)}
              target="_blank"
              rel="noopener noreferrer"
            >
              {String(r.url)}
            </a>
          )}
        </div>
      ))}
    </div>
  );
}

function ProseResult({ result }: { result: Record<string, unknown> }) {
  const text = String(result.analysis || result.report || result.content || "");
  return (
    <div className="tool-result-prose">
      <Markdown>{text}</Markdown>
    </div>
  );
}

function StatusResult({
  functionName,
  result,
  cancelled,
  onFileClick,
}: {
  functionName: string;
  result: unknown;
  cancelled: boolean;
  onFileClick?: (filename: string) => void;
}) {
  if (cancelled) {
    return (
      <div className="tool-header">
        <div className="tool-dot-outlined" />
        <span className="tool-name-cancelled">{functionName.toUpperCase()}</span>
        <span className="tool-status-chip tool-status-cancelled">CANCELLED</span>
      </div>
    );
  }

  const obj = (result as Record<string, unknown>) || {};
  const isError = !!obj.error;
  const subject = String(obj.error || obj.path || obj.message || obj.title || "");
  const isFile = !isError && obj.path && onFileClick;
  const filename = obj.path ? String(obj.path).split("/").pop() || "" : "";

  return (
    <div className="tool-header">
      <div className={isError ? "tool-dot-danger" : "tool-dot"} />
      <span className={isError ? "tool-name-danger" : "tool-name"}>
        {functionName.toUpperCase()}
      </span>
      {subject && (
        <span
          className={`tool-subject ${isFile ? "tool-subject-link" : ""}`}
          onClick={isFile ? () => onFileClick(filename) : undefined}
        >
          {subject}
        </span>
      )}
      <span
        className={`tool-status-chip ${isError ? "tool-status-denied" : "tool-status-ok"}`}
      >
        {isError ? "DENIED" : "OK"}
      </span>
    </div>
  );
}

function RawResult({ result, functionName }: { result: unknown; functionName: string }) {
  const json = JSON.stringify(result, null, 2);
  return (
    <div>
      <div className="tool-header">
        <div className="tool-dot" />
        <span className="tool-name">{functionName.toUpperCase()}</span>
        <button
          className="tool-result-copy"
          onClick={() => navigator.clipboard.writeText(json)}
        >
          COPY
        </button>
      </div>
      <div className="tool-result-raw vx-scroll" style={{ marginTop: 8 }}>
        {json}
      </div>
    </div>
  );
}

export function ToolResultCard({
  functionName,
  result,
  cancelled,
  latencyMs,
  onFileClick,
}: Props) {
  const parsed = tryParseJson(result);
  const kind = classify(result, cancelled);

  if (kind === "status") {
    return (
      <StatusResult
        functionName={functionName}
        result={parsed}
        cancelled={cancelled}
        onFileClick={onFileClick}
      />
    );
  }

  const obj = parsed as Record<string, unknown>;
  const meta: string[] = [];
  if (latencyMs) meta.push(formatLatency(latencyMs));
  if (kind === "results") {
    const items = (obj.results || obj.files || obj.issues) as unknown[];
    if (Array.isArray(items)) {
      const label = Array.isArray(obj.files)
        ? "FILES"
        : Array.isArray(obj.issues)
          ? "ISSUES"
          : "RESULTS";
      meta.push(`${items.length} ${label}`);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div className="tool-header">
        <div className="tool-dot" />
        <span className="tool-name">{functionName.toUpperCase()}</span>
        {meta.length > 0 && (
          <span className="tool-meta">{meta.join(" · ")}</span>
        )}
      </div>
      {kind === "results" && <ResultsList result={obj} onFileClick={onFileClick} />}
      {kind === "prose" && (
        typeof parsed === "string"
          ? <div className="tool-result-prose">{parsed}</div>
          : <ProseResult result={obj} />
      )}
      {kind === "raw" && <RawResult result={parsed} functionName={functionName} />}
    </div>
  );
}
