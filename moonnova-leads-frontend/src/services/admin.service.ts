import { api } from "@/lib/api";
import type {
  AdminAiJob,
  AdminAiSummary,
  AdminOverview,
  AdminSearch,
  AdminUser,
  MonitoringEvent,
  PaginatedResponse,
  SystemHealth
} from "@/types/admin";

function normalizeList<T>(data: PaginatedResponse<T> | T[]): T[] {
  if (Array.isArray(data)) return data;
  return data.results || [];
}

export const adminService = {
  async getOverview() {
    const response = await api.get<AdminOverview>("/admin-dashboard/overview/");
    return response.data;
  },

  async getUsers() {
    const response = await api.get<PaginatedResponse<AdminUser> | AdminUser[]>(
      "/admin-dashboard/users/",
      {
        params: {
          page_size: 50
        }
      }
    );

    return normalizeList(response.data);
  },

  async getSystemHealth() {
    const response = await api.get<SystemHealth>(
      "/admin-dashboard/system-health/"
    );

    return response.data;
  },

  async getMonitoringEvents() {
    const response = await api.get<
      PaginatedResponse<MonitoringEvent> | MonitoringEvent[]
    >("/monitoring/events/", {
      params: {
        page_size: 30
      }
    });

    return normalizeList(response.data);
  },

  async getAiSummary() {
    const response = await api.get<AdminAiSummary>(
      "/ai/usage/"
    );

    return response.data;
  },

  async getAiJobs() {
    const response = await api.get<PaginatedResponse<AdminAiJob> | AdminAiJob[]>(
      "/ai/jobs/",
      {
        params: {
          page_size: 30
        }
      }
    );

    return normalizeList(response.data);
  },

  async getSearches() {
    const response = await api.get<PaginatedResponse<AdminSearch> | AdminSearch[]>(
      "/admin-dashboard/searches/",
      {
        params: {
          page_size: 30
        }
      }
    );

    return normalizeList(response.data);
  },

  async activateUser(userId: number | string) {
    const response = await api.post(`/admin-dashboard/users/${userId}/activate/`);
    return response.data;
  },

  async suspendUser(userId: number | string) {
    const response = await api.post(`/admin-dashboard/users/${userId}/suspend/`);
    return response.data;
  }
};