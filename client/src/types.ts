export type ActivityEntry =
  | { kind: "user"; text: string; timestamp: number }
  | { kind: "bot"; text: string; timestamp: number }
  | {
      kind: "tool-start";
      functionName: string;
      toolCallId: string;
      timestamp: number;
    }
  | {
      kind: "tool-result";
      functionName: string;
      toolCallId: string;
      result: unknown;
      cancelled: boolean;
      timestamp: number;
    };
