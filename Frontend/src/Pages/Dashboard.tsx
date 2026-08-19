import { useEffect, useState } from "react";
import { useAnalysis } from "../Services/Context/AnalyseCont";
import { Layout } from "../Components/Layout";
import { UploadZone } from "../Components/UploadZone";
import { RiskScoreCard } from "../Components/RiskScoreCard";
import { AnomalyList } from "../Components/AnomalyList";
import { Heatmap } from "../Components/HeatMap";
import { ReportGenerator } from "../Components/ReportGenerator";
import { uploadFile, startAnalysis, getResults, getHistory } from "../Services/api";
import type { HistoryItem } from "../Services/api";

const MAX_POLL_ATTEMPTS = 60;

const statusBadge = (status: string) =>
  status === "done"
    ? "badge-success"
    : status === "error"
    ? "badge-critical"
    : "badge-warning";

const statusLabel = (status: string) =>
  status === "done" ? "Terminé" : status === "error" ? "Erreur" : "En cours";

export const Dashboard = () => {
  const { analysisId, results, status, setFileId, setAnalysisId, setResults, setStatus } = useAnalysis();
  const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    getHistory().then((res) => setHistory(res.data)).catch(() => {});
  }, []);

  const handleUpload = async (file: File) => {
    setErrorMessage("");
    try {
      setStatus("uploading");
      const res = await uploadFile(file);
      const id = res.data.file_id;
      setFileId(id);
      setStatus("analyzing");

      const analysisRes = await startAnalysis(id);
      const aId = analysisRes.data.analysis_id;
      setAnalysisId(aId);

      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const resultRes = await getResults(aId);
          if (resultRes.data.status === "done") {
            setResults(resultRes.data);
            setStatus("done");
            clearInterval(interval);
            setPollInterval(null);
            setErrorMessage("");
            getHistory().then((r) => setHistory(r.data)).catch(() => {});
          } else if (attempts >= MAX_POLL_ATTEMPTS) {
            clearInterval(interval);
            setPollInterval(null);
            setStatus("error");
            setErrorMessage("Le traitement a pris trop de temps. Réessayez.");
          }
        } catch {
          clearInterval(interval);
          setPollInterval(null);
          setStatus("error");
          setErrorMessage("Erreur lors de la récupération des résultats.");
        }
      }, 2000);
      setPollInterval(interval);
    } catch (e: any) {
      setStatus("error");
      const detail = e?.response?.data?.detail || e?.message || "Erreur inconnue";
      setErrorMessage(detail);
      console.error("Upload/analyze error:", e);
    }
  };

  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  const heatmapData = results?.anomalies
    ? Object.entries(
        results.anomalies.reduce<Record<string, number>>((acc, a: { type: string; severity: string }) => {
          acc[a.type] = (acc[a.type] || 0) + 1;
          return acc;
        }, {})
      ).map(([category, count]) => ({ category, risk_level: count }))
    : [];

  return (
    <Layout>
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <h1 className="page-title">Audit de conformité</h1>
          <p className="text-gray-500 text-sm mt-1">Analysez vos données financières avec nos agents IA</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <UploadZone onUpload={handleUpload} isLoading={status === "uploading" || status === "analyzing"} />

          {status === "analyzing" && (
            <div className="card p-5 flex items-center justify-center gap-3 text-cyan-400 border-cyan-500/20">
              <svg className="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <p className="text-sm animate-pulse">Les agents IA analysent vos données...</p>
            </div>
          )}
          {status === "done" && results && (
            <div className="space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-green-400 bg-success/10 border border-success/25 p-4 rounded-xl text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Audit terminé pour {results.filename}
              </div>
              {analysisId && <ReportGenerator analysisId={analysisId} />}
            </div>
          )}
          {status === "error" && (
            <div className="text-danger text-sm bg-danger/10 border border-danger/25 rounded-xl p-4 text-center">
              Erreur lors du traitement. {errorMessage || "Vérifiez le fichier."}
            </div>
          )}

          {results && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fadeIn">
              <RiskScoreCard score={results.risk_score} />
              <Heatmap data={heatmapData} />
              <div className="md:col-span-2">
                <AnomalyList anomalies={results.anomalies || []} />
              </div>
            </div>
          )}
        </div>

        <div>
          <div className="card p-6 sticky top-24">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title">Historique</h3>
              {history.length > 0 && (
                <span className="badge-info badge">{history.length}</span>
              )}
            </div>
            {history.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">Aucune analyse pour le moment</p>
            ) : (
              <div className="space-y-3 max-h-[65vh] overflow-y-auto pr-1">
                {history.map((item) => (
                  <div key={item.id} className="row">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-gray-200 truncate font-medium">{item.filename}</p>
                      <span className={`badge shrink-0 ${statusBadge(item.status)}`}>{statusLabel(item.status)}</span>
                    </div>
                    {item.status === "done" && (
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-[11px] text-gray-500">{new Date(item.created_at).toLocaleDateString()}</span>
                        <span className="text-xs font-semibold text-cyan-400">Score: {item.risk_score}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
