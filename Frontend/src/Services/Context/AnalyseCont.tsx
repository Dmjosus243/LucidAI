import { createContext, useContext, useState, type ReactNode } from "react";

export interface Anomaly {
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  reference?: Record<string, unknown>;
}

export interface AnalysisResult {
  status: "done" | "pending";
  risk_score?: number;
  anomalies?: Anomaly[];
  report_path?: string;
  filename?: string;
}

type AnalysisStatus = "idle" | "uploading" | "analyzing" | "done" | "error";

interface AnalysisContextType {
  fileId: string | null;
  analysisId: string | null;
  results: AnalysisResult | null;
  status: AnalysisStatus;
  setFileId: (id: string) => void;
  setAnalysisId: (id: string) => void;
  setResults: (data: AnalysisResult) => void;
  setStatus: (status: AnalysisStatus) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider = ({ children }: { children: ReactNode }) => {
  const [fileId, setFileId] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>("idle");

  return (
    <AnalysisContext.Provider value={{ fileId, analysisId, results, status, setFileId, setAnalysisId, setResults, setStatus }}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) throw new Error("useAnalysis must be used within AnalysisProvider");
  return context;
};
