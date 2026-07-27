import { useEffect, useState } from "react";
import { useAnalysis } from "../context/AnalysisContext";
import { UploadZone } from "../components/UploadZone";
import { RiskScoreCard } from "../components/RiskScoreCard";
import { AnomalyList } from "../components/AnomalyList";
import { Heatmap } from "../components/Heatmap";
import { ReportGenerator } from "../components/ReportGenerator";
import { uploadFile, startAnalysis, getResults } from "../services/api";

export const Dashboard = () => {
  const { fileId, analysisId, results, status, setFileId, setAnalysisId, setResults, setStatus } = useAnalysis();
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  const handleUpload = async (file: File) => {
    try {
      setStatus("uploading");
      const res = await uploadFile(file);
      const id = res.data.file_id;
      setFileId(id);
      setStatus("analyzing");
      
      // Lancer l'analyse
      const analysisRes = await startAnalysis(id);
      const analysisId = analysisRes.data.analysis_id;
      setAnalysisId(analysisId);
      
      // Polling des résultats
      const interval = setInterval(async () => {
        const resultRes = await getResults(analysisId);
        if (resultRes.data.status === "done") {
          setResults(resultRes.data);
          setStatus("done");
          clearInterval(interval);
          setPollInterval(null);
        }
      }, 2000);
      setPollInterval(interval);
    } catch (e) {
      setStatus("error");
      console.error(e);
    }
  };

  // Nettoyage
  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  return (
    <div className="min-h-screen p-6 md:p-12">
      <header className="flex justify-between items-center mb-12">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center font-bold text-dark">L</div>
          <h1 className="text-2xl font-bold text-white">LucidAI</h1>
        </div>
        <div className="text-sm text-gray-400">Audit Intelligence</div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
        {/* Colonne de Gauche - Upload */}
        <div>
          <UploadZone onUpload={handleUpload} isLoading={status === "uploading" || status === "analyzing"} />
          
          {status === "analyzing" && (
            <div className="mt-4 text-center text-cyan-400 animate-pulse">⚡ Les agents IA analysent vos données...</div>
          )}

          {status === "done" && results && (
            <div className="mt-6">
              <div className="text-sm text-green-400 bg-green-400/10 p-3 rounded-xl text-center">
                ✅ Audit terminé pour {results.filename}
              </div>
              {analysisId && <ReportGenerator analysisId={analysisId} />}
            </div>
          )}

          {status === "error" && (
            <div className="mt-4 text-center text-danger">❌ Erreur lors du traitement. Vérifiez le fichier.</div>
          )}
        </div>

        {/* Colonne de Droite - Résultats */}
        <div className="space-y-6">
          {results ? (
            <>
              <RiskScoreCard score={results.risk_score} />
              <Heatmap data={results.anomalies?.map((a: any) => ({ category: a.type, risk_level: 50 })) || []} />
              <AnomalyList anomalies={results.anomalies || []} />
            </>
          ) : (
            <div className="glass rounded-2xl p-12 text-center text-gray-500 h-full flex items-center justify-center">
              <div>
                <p className="text-4xl mb-4">📊</p>
                <p>Les résultats d'audit apparaîtront ici</p>
                <p className="text-sm">Téléchargez un fichier pour commencer</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};