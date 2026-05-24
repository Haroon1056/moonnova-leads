import { api } from "@/lib/api";
import type {
  AiInsight,
  AiJob,
  AiJobListResponse,
  AiUsage,
  BulkAiPayload,
  SingleAiPayload
} from "@/types/ai";

function normalizeAiJobs(data: AiJobListResponse | AiJob[]): AiJob[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

export const aiService = {
  async getUsage() {
    const response = await api.get<AiUsage>("/ai/usage/");
    return response.data;
  },

  async getLeadInsight(leadId: number | string) {
    const response = await api.get<AiInsight>(`/ai/leads/${leadId}/insight/`);
    return response.data;
  },

  async generateLeadInsight(leadId: number | string, payload: SingleAiPayload) {
    const response = await api.post<AiInsight>(
      `/ai/leads/${leadId}/insight/`,
      payload
    );

    return response.data;
  },

  async bulkGenerate(payload: BulkAiPayload) {
    const response = await api.post<AiJob>("/ai/bulk-generate/", payload);
    return response.data;
  },

  async getJobs() {
    const response = await api.get<AiJobListResponse | AiJob[]>("/ai/jobs/");
    return normalizeAiJobs(response.data);
  },

  async getJob(id: number | string) {
    const response = await api.get<AiJob>(`/ai/jobs/${id}/`);
    return response.data;
  }
};