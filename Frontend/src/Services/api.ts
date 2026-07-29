import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_URL });

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      delete api.defaults.headers.common["Authorization"];
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export interface UploadResponse {
  file_id: string;
  preview: Record<string, unknown>[];
  filename: string;
}

export interface AnalysisResultResponse {
  status: "done" | "pending";
  risk_score?: number;
  anomalies?: { type: string; severity: "critical" | "high" | "medium" | "low"; description: string }[];
  report_path?: string;
  filename?: string;
}

export interface HistoryItem {
  id: string;
  filename: string;
  status: string;
  risk_score: number;
  created_at: string;
}

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const startAnalysis = async (fileId: string) => {
  return api.post<{ analysis_id: string; status: string }>(`/analyze/${fileId}`);
};

export const getResults = async (analysisId: string) => {
  return api.get<AnalysisResultResponse>(`/results/${analysisId}`);
};

export const downloadReport = async (analysisId: string) => {
  return api.get(`/report/${analysisId}/pdf`, { responseType: "blob" });
};

export const getHistory = async (skip = 0, limit = 20) => {
  return api.get<HistoryItem[]>("/history", { params: { skip, limit } });
};
