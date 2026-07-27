import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_URL });

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
};

export const startAnalysis = async (fileId: string) => {
  return api.post(`/analyze/${fileId}`);
};

export const getResults = async (analysisId: string) => {
  return api.get(`/results/${analysisId}`);
};

export const downloadReport = async (analysisId: string) => {
  return api.get(`/report/${analysisId}/pdf`, { responseType: "blob" });
};