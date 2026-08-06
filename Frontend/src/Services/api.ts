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

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  organization_id: string | null;
  created_at?: string;
  temporary_password?: string;
}

export interface OrganizationInfo {
  id: string;
  name: string;
  subscription_tier: string;
  created_at?: string;
  member_count?: number;
}

export interface AuditLogItem {
  id: string;
  user_id: string | null;
  action: string;
  details: Record<string, unknown>;
  ip_address?: string;
  created_at?: string;
}

export interface AdminStats {
  total_users: number;
  total_organizations: number;
  total_analyses: number;
  avg_risk_score: number;
  organizations_by_tier: Record<string, number>;
  users_by_role: Record<string, number>;
}

export interface OrgAnalysis {
  id: string;
  filename: string;
  status: string;
  risk_score: number;
  user_id: string;
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

export const getUsers = async () => {
  return api.get<User[]>("/users");
};

export const inviteUser = async (data: { email: string; full_name: string; role: string; password?: string }) => {
  return api.post<User>("/users", data);
};

export const updateUser = async (userId: string, data: { role?: string; is_active?: boolean; full_name?: string }) => {
  return api.patch<User>(`/users/${userId}`, data);
};

export const deleteUser = async (userId: string) => {
  return api.delete(`/users/${userId}`);
};

export const getOrganization = async () => {
  return api.get<OrganizationInfo | null>("/organizations/me");
};

export const updateOrganization = async (data: { name?: string; subscription_tier?: string }) => {
  return api.patch<OrganizationInfo>("/organizations/me", data);
};

export const getOrgAnalyses = async () => {
  return api.get<OrgAnalysis[]>("/analyses/org");
};

export const getAuditLogs = async (limit = 100) => {
  return api.get<AuditLogItem[]>("/audit-logs", { params: { limit } });
};

export const getAdminStats = async () => {
  return api.get<AdminStats>("/admin/stats");
};

export const forgotPassword = async (email: string) => {
  return api.post<{ ok: boolean }>("/auth/forgot-password", { email });
};

export const resetPassword = async (email: string, otp: string, new_password: string) => {
  return api.post<{ ok: boolean; message: string }>("/auth/reset-password", { email, otp, new_password });
};
