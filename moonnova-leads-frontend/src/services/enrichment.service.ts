import { api } from "@/lib/api";
import type {
  EnrichmentJob,
  EnrichmentJobListResponse
} from "@/types/enrichment";

function normalizeJobs(
  data: EnrichmentJobListResponse | EnrichmentJob[]
): EnrichmentJob[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

export const enrichmentService = {
  async getJobs() {
    const response = await api.get<EnrichmentJobListResponse | EnrichmentJob[]>(
      "/leads/enrichment-jobs/"
    );

    return normalizeJobs(response.data);
  },

  async getSearchEnrichmentJob(searchId: number | string) {
    const jobs = await this.getJobs();

    const matchingJobs = jobs
      .filter((job) => Number(job.search) === Number(searchId))
      .sort((a, b) => {
        const dateA = new Date(a.created_at || 0).getTime();
        const dateB = new Date(b.created_at || 0).getTime();
        return dateB - dateA;
      });

    return matchingJobs[0] || null;
  },

  async startSearchEnrichment(searchId: number | string) {
    const response = await api.post(
      `/leads/search/${searchId}/enrich-website/`,
      {
        force: false
      }
    );

    return response.data;
  }
};