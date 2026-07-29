import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAnalysis } from "../Services/Context/AnalyseCont";
import { useAuth } from "../Services/Context/AuthContext";
import { UploadZone } from "../Components/UploadZone";
import { RiskScoreCard } from "../Components/RiskScoreCard";
import { AnomalyList } from "../Components/AnomalyList";
import { Heatmap } from "../Components/HeatMap";
import { ReportGenerator } from "../Components/ReportGenerator";
import { uploadFile, startAnalysis, getResults, getHistory } from "../Services/api";
import type { HistoryItem } from "../Services/api";

const MAX_POLL_ATTEMPTS = 60;

export const Dashboard = () => {
  const { analysisId, results, status, setFileId, setAnalysisId, setResults, setStatus } = useAnalysis();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    getHistory().then((res) => setHistory(res.data)).catch(() => {});
  }, []);

  const handleUpload = async (file: File) => {
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
            getHistory().then((r) => setHistory(r.data)).catch(() => {});
          } else if (attempts >= MAX_POLL_ATTEMPTS) {
            clearInterval(interval);
            setPollInterval(null);
            setStatus("error");
          }
        } catch {
          clearInterval(interval);
          setPollInterval(null);
          setStatus("error");
        }
      }, 2000);
      setPollInterval(interval);
    } catch (e) {
      setStatus("error");
      console.error(e);
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
    <div className="min-h-screen p-6 md:p-12">
      <header className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center font-bold text-dark">L</div>
          <h1 className="text-2xl font-bold text-white">LucidAI</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{user?.full_name}</span>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="text-sm text-gray-500 hover:text-danger transition-colors"
          >
            Déconnexion
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
        <div className="lg:col-span-2">
          <UploadZone onUpload={handleUpload} isLoading={status === "uploading" || status === "analyzing"} />
          
          {status === "analyzing" && (
            <div className="mt-4 text-center text-cyan-400 animate-pulse">Les agents IA analysent vos données...</div>
          )}
          {status === "done" && results && (
            <div className="mt-6">
              <div className="text-sm text-green-400 bg-green-400/10 p-3 rounded-xl text-center">
                Audit terminé pour {results.filename}
              </div>
              {analysisId && <ReportGenerator analysisId={analysisId} />}
            </div>
          )}
          {status === "error" && (
            <div className="mt-4 text-center text-danger">Erreur lors du traitement. Vérifiez le fichier.</div>
          )}

          {results && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <RiskScoreCard score={results.risk_score} />
              <Heatmap data={heatmapData} />
              <div className="md:col-span-2">
                <AnomalyList anomalies={results.anomalies || []} />
              </div>
            </div>
          )}
        </div>

        <div>
          <div className="glass rounded-2xl p-6">
            <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Historique</h3>
            {history.length === 0 ? (
              <p className="text-gray-500 text-sm">Aucune analyse pour le moment</p>
            ) : (
              <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                {history.map((item) => (
                  <div key={item.id} className="p-3 bg-dark/30 rounded-lg">
                    <p className="text-sm text-gray-200 truncate">{item.filename}</p>
                    <div className="flex justify-between items-center mt-1">
                      <span className={`text-xs ${item.status === "done" ? "text-success" : item.status === "error" ? "text-danger" : "text-yellow-400"}`}>
                        {item.status === "done" ? "Terminé" : item.status === "error" ? "Erreur" : "En cours"}
                      </span>
                      {item.status === "done" && (
                        <span className="text-xs text-gray-400">Score: {item.risk_score}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
