import { createContext, useContext, useState, ReactNode } from "react";

interface AnalysisContextType {
  fileId: string | null;
  analysisId: string | null;
  results: any | null;
  status: "idle" | "uploading" | "analyzing" | "done" | "error";
  setFileId: (id: string) => void;
  setAnalysisId: (id: string) => void;
  setResults: (data: any) => void;
  setStatus: (status: any) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider = ({ children }: { children: ReactNode }) => {
  const [fileId, setFileId] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [results, setResults] = useState<any | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "analyzing" | "done" | "error">("idle");

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