import { api } from "@/lib/api";
import type { UsageSummary } from "@/types/usage";

export const usageService = {
  async getMyUsage() {
    const response = await api.get<UsageSummary>("/usage/me/");
    return response.data;
  }
};
