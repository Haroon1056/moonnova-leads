import { api } from "@/lib/api";
import type {
  CreateExportPayload,
  ExportHistory,
  ExportHistoryListResponse
} from "@/types/export";

function normalizeExportList(
  data: ExportHistoryListResponse | ExportHistory[]
): ExportHistory[] {
  if (Array.isArray(data)) return data;

  return data.results || [];
}

function getFilenameFromContentDisposition(
  contentDisposition?: string
): string | null {
  if (!contentDisposition) return null;

  const filenameStarMatch = contentDisposition.match(
    /filename\*=UTF-8''([^;]+)/i
  );

  if (filenameStarMatch?.[1]) {
    return decodeURIComponent(filenameStarMatch[1]);
  }

  const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/i);

  if (filenameMatch?.[1]) {
    return filenameMatch[1];
  }

  return null;
}

export const exportService = {
  async createExport(payload: CreateExportPayload) {
    const response = await api.post<any>("/leads/exports/", payload);

    return response.data.export || response.data;
  },

  async getExports() {
    const response = await api.get<ExportHistoryListResponse | ExportHistory[]>(
      "/leads/export-history/"
    );

    return normalizeExportList(response.data);
  },

  async getExport(id: number | string) {
    const response = await api.get<ExportHistory>(`/leads/exports/${id}/`);

    return response.data;
  },

  async downloadExport(exportItem: ExportHistory) {
    const response = await api.get(`/leads/exports/${exportItem.id}/download/`, {
      responseType: "blob"
    });

    const contentType =
      (response.headers["content-type"] as string | undefined) ||
      "application/octet-stream";

    const contentDisposition = response.headers["content-disposition"] as
      | string
      | undefined;

    const filenameFromHeader =
      getFilenameFromContentDisposition(contentDisposition);

    const fallbackName =
      exportItem.file_name ||
      `moonnova-export-${exportItem.id}.${
        exportItem.file_format || exportItem.export_type || "csv"
      }`;

    const fileName = filenameFromHeader || fallbackName;

    const blob = new Blob([response.data], {
      type: contentType
    });

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;

    document.body.appendChild(link);
    link.click();

    link.remove();
    window.URL.revokeObjectURL(url);

    return true;
  },

  async deleteExport(id: number | string) {
    const response = await api.delete(`/leads/exports/${id}/delete/`);

    return response.data;
  }
};