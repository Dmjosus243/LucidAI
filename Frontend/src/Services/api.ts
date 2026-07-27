import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_URL });

export interface UploadResponse {
  file_id: string;
  preview: Record<string, unknown>[];
  filename: string;
}

export interface AnalysisStartResponse {
  analysis_id: string;
  status: string;
}

export interface AnalysisResultResponse {
  status: "done" | "pending";
  risk_score?: number;
  anomalies?: { type: string; severity: string; description: string }[];
  report_path?: string;
  filename?: string;
}

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<UploadResponse>("/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
};

export const startAnalysis = async (fileId: string) => {
  return api.post<AnalysisStartResponse>(`/analyze/${fileId}`);
};

export const getResults = async (analysisId: string) => {
  return api.get<AnalysisResultResponse>(`/results/${analysisId}`);
};

export const downloadReport = async (analysisId: string) => {
  return api.get(`/report/${analysisId}/pdf`, { responseType: "blob" });
};
