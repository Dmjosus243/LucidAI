import React, { useState } from 'react';
import { useAnalysisPoll } from '../hooks/useAnalysisPoll';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const InvoiceUploader: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any[] | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Hook de polling pour l'analyse asynchrone
  const { result, status: analysisStatus, error: pollError } = useAnalysisPoll(analysisId, API_BASE_URL);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setPreview(null);
      setAnalysisId(null);
      setUploadError(null);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      // 1. Upload vers Supabase Storage via /api/v1/upload
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadRes = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        const errData = await uploadRes.json();
        throw new Error(errData.detail || "Échec du téléversement.");
      }

      const uploadData = await uploadRes.json();
      setPreview(uploadData.preview);

      // 2. Démarrage de l'analyse via /api/v1/analyze/{file_id}
      const analyzeRes = await fetch(`${API_BASE_URL}/analyze/${uploadData.file_id}`, {
        method: 'POST',
      });

      if (!analyzeRes.ok) {
        const errData = await analyzeRes.json();
        throw new Error(errData.detail || "Échec du lancement de l'analyse.");
      }

      const analyzeData = await analyzeRes.json();

      // 3. Stocker l'analysis_id pour démarrer le polling
      setAnalysisId(analyzeData.analysis_id);

    } catch (err: any) {
      setUploadError(err.message || "Une erreur est survenue.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        Analyse Comptable & Détection d'Anomalies (LucidAI)
      </h2>

      {/* Sélection de fichier */}
      <div className="flex flex-col sm:flex-row items-center gap-4 mb-6">
        <input
          type="file"
          accept=".csv, .xlsx, .xls"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2.5 file:px-4
            file:rounded-lg file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100
            dark:file:bg-gray-700 dark:file:text-gray-300"
        />
        <button
          onClick={handleUploadAndAnalyze}
          disabled={!selectedFile || isUploading || analysisStatus === 'processing'}
          className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50 whitespace-nowrap"
        >
          {isUploading ? 'Envoi...' : 'Lancer l\'analyse'}
        </button>
      </div>

      {/* Message d'erreur initial */}
      {uploadError && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-50 rounded-lg dark:bg-red-900/30 dark:text-red-400">
          {uploadError}
        </div>
      )}

      {/* Aperçu des données importées */}
      {preview && preview.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Aperçu des premières lignes
          </h3>
          <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
            <table className="min-w-full text-xs text-left text-gray-500 dark:text-gray-400">
              <thead className="bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 uppercase">
                <tr>
                  {Object.keys(preview[0]).map((col) => (
                    <th key={col} className="px-3 py-2 border-b">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, idx) => (
                  <tr key={idx} className="border-b dark:border-gray-700">
                    {Object.values(row).map((val: any, i) => (
                      <td key={i} className="px-3 py-2">{val ?? '-'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* État du Polling */}
      <div className="space-y-4">
        {analysisStatus === 'processing' && (
          <div className="flex items-center p-4 bg-blue-50 dark:bg-blue-950/40 rounded-lg text-blue-700 dark:text-blue-300">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Analyse par l'IA en cours... Veuillez patienter.</span>
          </div>
        )}

        {(pollError || analysisStatus === 'error') && (
          <div className="p-4 text-sm text-red-700 bg-red-50 rounded-lg dark:bg-red-900/30 dark:text-red-400">
            {pollError || 'Erreur pendant l\'analyse.'}
          </div>
        )}

        {analysisStatus === 'done' && result && (
          <div className="p-5 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-green-800 dark:text-green-300">
                Analyse terminée avec succès
              </h3>
              <span className="px-3 py-1 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-100 font-semibold rounded-full text-xs">
                Score de risque : {result.risk_score ?? 0}
              </span>
            </div>

            {/* Liste des anomalies */}
            {result.anomalies && result.anomalies.length > 0 ? (
              <div className="mt-3">
                <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">Anomalies détectées :</h4>
                <ul className="list-disc pl-5 text-sm text-gray-700 dark:text-gray-300 space-y-1">
                  {result.anomalies.map((anom, i) => (
                    <li key={i}>
                      {typeof anom === 'string' ? anom : (anom.description || JSON.stringify(anom))}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">Aucune anomalie critique n'a été détectée.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};