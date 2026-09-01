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
  anomalies?: {
    type: string;
    severity: "critical" | "high" | "medium" | "low";
    description: string;
    confidence?: number;
    summary?: string;
    reason?: string;
    red_flags?: string[];
    suggested_action?: string;
  }[];
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
  return api.post<{ analysis_id: string; status: string }>(`/analyze/${fileId}`, null, { timeout: 300000 });
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

export interface AuditLogPage {
  total: number;
  items: AuditLogItem[];
}

export const getAuditLogs = async (limit = 100, skip = 0, action?: string) => {
  return api.get<AuditLogPage>("/audit-logs", { params: { limit, skip, action } });
};

export const exportAuditLogs = async () => {
  return api.get("/audit-logs/export", { responseType: "blob" });
};

export const getAdminStats = async () => {
  return api.get<AdminStats>("/admin/stats");
};

export interface OrgWithMembers {
  id: string;
  name: string;
  subscription_tier: string;
  created_at: string | null;
  analyses_count: number;
  members: User[];
}

export const getAdminOrganizations = async () => {
  return api.get<OrgWithMembers[]>("/admin/organizations");
};

export const createCheckoutSession = async (plan: string) => {
  return api.post<{ checkout_url: string; transaction_ref: string }>("/billing/checkout", { plan });
};

export const forgotPassword = async (email: string) => {
  return api.post<{ ok: boolean }>("/auth/forgot-password", { email });
};

export const resetPassword = async (email: string, otp: string, new_password: string) => {
  return api.post<{ ok: boolean; message: string }>("/auth/reset-password", { email, otp, new_password });
};

// ----------------------------------------------------------------------
// Feature 1 — OCR + validation humaine
// ----------------------------------------------------------------------
export interface OcrLine {
  label: string;
  date?: string | null;
  amount?: number | null;
  tax_rate?: number | null;
  confidence: number;
}

export interface OCRDocument {
  id: string;
  filename: string;
  status: "pending" | "validated" | "rejected";
  engine: string;
  confidence: number;
  lines: OcrLine[];
  created_at?: string;
}

export interface JournalEntry {
  id: string;
  entry_ref: string;
  date?: string | null;
  source: string;
  confidence: number;
  status: string;
  lines: { label: string; amount: number; tax_rate?: number }[];
  created_at?: string;
}

export const uploadOcrDocument = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<OCRDocument>("/ocr/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getOcrDocuments = async () => {
  return api.get<OCRDocument[]>("/ocr/documents");
};

export const validateOcrDocument = async (docId: string, lines: OcrLine[]) => {
  return api.post<{ ok: boolean; doc_id: string; entries: string[] }>(`/ocr/documents/${docId}/validate`, { lines });
};

export const rejectOcrDocument = async (docId: string) => {
  return api.post<{ ok: boolean; doc_id: string }>(`/ocr/documents/${docId}/reject`);
};

export const getJournalEntries = async (limit = 200) => {
  return api.get<JournalEntry[]>("/ocr/entries", { params: { limit } });
};

// ----------------------------------------------------------------------
// Feature 2 — Rapprochement bancaire automatisé
// ----------------------------------------------------------------------
export interface ReconResult {
  status: "auto" | "matched" | "unmatched";
  confidence: number;
  entry_index: number | null;
  statement_index: number | null;
  statement_line?: { date?: string; description?: string; amount?: number } | null;
}

export interface ReconImportResponse {
  statement_id: string;
  account_id: string;
  lines_count: number;
  automation_rate: number;
  results: ReconResult[];
}

export interface BankStatementItem {
  id: string;
  account_id: string | null;
  date_range: string | null;
  source: string;
  lines_count: number;
  created_at?: string;
}

export const importStatement = async (file: File, accountId?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  if (accountId) formData.append("account_id", accountId);
  return api.post<ReconImportResponse>("/recon/import", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getStatements = async () => {
  return api.get<BankStatementItem[]>("/recon/statements");
};

// ----------------------------------------------------------------------
// Feature 5 — Assistant conversationnel
// ----------------------------------------------------------------------
export interface ChatSessionItem {
  id: string;
  title: string;
  created_at?: string;
}

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode?: string;
  created_at?: string;
}

export const createChatSession = async (title?: string) => {
  return api.post<ChatSessionItem>("/chat/sessions", { title });
};

export const getChatSessions = async () => {
  return api.get<ChatSessionItem[]>("/chat/sessions");
};

export const getChatMessages = async (sessionId: string) => {
  return api.get<ChatMessageItem[]>(`/chat/sessions/${sessionId}/messages`);
};

export const sendChatMessage = async (
  sessionId: string,
  content: string
) => {
  return api.post<{
    user_message: ChatMessageItem;
    assistant_message: ChatMessageItem;
  }>(`/chat/sessions/${sessionId}/messages`, { content });
};

// ----------------------------------------------------------------------
// Feature 7 — APIs bancaires & webhooks
// ----------------------------------------------------------------------
export interface BankAccountItem {
  id: string;
  label: string;
  bank_code: string | null;
  currency: string;
  provider: string;
  last_sync_at?: string | null;
}

export interface WebhookEventItem {
  id: string;
  provider: string;
  event_type: string | null;
  status: string;
  payload: Record<string, unknown>;
  received_at?: string | null;
}

export const createBankAccount = async (data: {
  label: string;
  bank_code?: string;
  currency?: string;
  provider?: string;
}) => {
  return api.post<BankAccountItem>("/banking/accounts", data);
};

export const getBankAccounts = async () => {
  return api.get<BankAccountItem[]>("/banking/accounts");
};

export const deleteBankAccount = async (accountId: string) => {
  return api.delete<{ ok: boolean }>(`/banking/accounts/${accountId}`);
};

export const getWebhookEvents = async (limit = 100) => {
  return api.get<WebhookEventItem[]>("/banking/webhook/events", { params: { limit } });
};

// ----------------------------------------------------------------------
// Feature 3 — Écritures prédictives (journal de caisse)
// ----------------------------------------------------------------------
export interface PredictedLine {
  label: string;
  account: string;
  debit?: number | null;
  credit?: number | null;
  amount?: number | null;
}

export interface PredictedEntryItem {
  id: string;
  entry_ref: string;
  date?: string;
  confidence: number;
  category?: string;
  description?: string;
  lines: PredictedLine[];
  status: "pending" | "validated" | "rejected";
  created_at?: string;
}

export interface CashOperationInput {
  date?: string;
  description: string;
  amount: number;
  direction: "in" | "out";
}

export const predictFromCash = async (operations: CashOperationInput[]) => {
  return api.post<{ created: PredictedEntryItem[]; count: number }>("/predict/from-cash", { operations });
};

export const getPredictions = async () => {
  return api.get<PredictedEntryItem[]>("/predict/pending");
};

export const validatePrediction = async (entryId: string) => {
  return api.post<{ ok: boolean; status: string }>(`/predict/${entryId}/validate`);
};

export const rejectPrediction = async (entryId: string) => {
  return api.post<{ ok: boolean; status: string }>(`/predict/${entryId}/reject`);
};
