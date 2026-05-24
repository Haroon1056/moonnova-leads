import { WS_URL } from "@/lib/constants";

export type RealtimeEventType =
  | "connected"
  | "notification"
  | "search_started"
  | "search_progress"
  | "search_completed"
  | "search_failed"
  | "lead_found"
  | "enrichment_started"
  | "enrichment_progress"
  | "lead_enriched"
  | "export_started"
  | "export_completed"
  | "export_failed"
  | "ai_job_started"
  | "ai_job_progress"
  | "ai_lead_completed"
  | "ai_job_completed"
  | "ai_job_failed";

export interface RealtimeEvent<T = unknown> {
  type: RealtimeEventType | string;
  data?: T;
  message?: string;
  search_id?: number;
  lead?: unknown;
}

export function createRealtimeSocket(accessToken: string) {
  const separator = WS_URL.includes("?") ? "&" : "?";
  const url = `${WS_URL}${separator}token=${accessToken}`;

  return new WebSocket(url);
}