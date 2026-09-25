import { useState, useEffect } from 'react';

export const useAnalysisPoll = (analysisId: string | null) => {
  const [data, setData] = useState<any>(null);
  const [status, setStatus] = useState<'idle' | 'processing' | 'done' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) {
      setStatus('idle');
      return;
    }

    setStatus('processing');
    const interval = setInterval(async () => {
      try {
        // Remplace par la route exacte de ton backend (ex: /api/v1/analysis/...)
        const response = await fetch(`http://localhost:8000/api/v1/analysis/${analysisId}`);
        const result = await response.json();

        if (result.status === 'done') {
          setData(result.data);
          setStatus('done');
          clearInterval(interval);
        } else if (result.status === 'error') {
          setError(result.message || "L'analyse a échoué.");
          setStatus('error');
          clearInterval(interval);
        }
      } catch (err) {
        setError("Erreur de connexion au serveur.");
        setStatus('error');
        clearInterval(interval);
      }
    }, 2500); // Requête toutes les 2.5 secondes

    return () => clearInterval(interval);
  }, [analysisId]);

  return { data, status, error };
};