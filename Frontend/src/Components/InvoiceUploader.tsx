import React, { useState } from 'react';
import { useAnalysisPoll } from '../hooks/useAnalysisPoll';

export const InvoiceUploader: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Utilisation du hook personnalisé
  const { data, status, error } = useAnalysisPoll(analysisId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setAnalysisId(null); // Réinitialiser pour un nouveau fichier
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Remplace par la route exacte de ton routeur upload.py
      const response = await fetch('http://localhost:8000/api/v1/upload', {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      
      if (response.ok && result.analysis_id) {
        setAnalysisId(result.analysis_id); // Déclenche le polling
      } else {
        alert("Erreur lors de l'upload");
      }
    } catch (err) {
      alert("Erreur réseau");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">
        Importer une facture
      </h2>
      
      <input 
        type="file" 
        accept=".pdf, .png, .jpg, .jpeg"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-500 mb-4
          file:mr-4 file:py-2 file:px-4
          file:rounded-md file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100"
      />

      <button 
        onClick={handleUpload} 
        disabled={!selectedFile || isUploading || status === 'processing'}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
      >
        {isUploading ? 'Envoi en cours...' : 'Analyser avec l\'IA'}
      </button>

      {/* Affichage des états d'analyse */}
      <div className="mt-6">
        {status === 'processing' && (
          <div className="flex items-center text-blue-600">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Extraction des données comptables en cours...
          </div>
        )}

        {status === 'error' && (
          <p className="text-red-500 font-semibold">{error}</p>
        )}

        {status === 'done' && data && (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded p-4">
            <h3 className="font-bold mb-2">Extraction réussie !</h3>
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};