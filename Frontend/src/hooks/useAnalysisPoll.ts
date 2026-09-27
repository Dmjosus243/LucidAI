import { useState, useEffect } from 'react';

export interface AnalysisResult {
  status: 'processing' | 'done' | 'error';
  risk_score?: number;
  anomalies?: Array<{
    type?: string;
    description?: string;
    severity?: string;
    row_index?: number;
  }>;
  report_path?: string;
  filename?: string;
  error?: string;
}

export const useAnalysisPoll = (
  analysisId: string | null, 
  baseUrl: string = 'http://localhost:8000/api/v1'
) => {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<'idle' | 'processing' | 'done' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) {
      setStatus('idle');
      setResult(null);
      setError(null);
      return;
    }

    setStatus('processing');
    setError(null);

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${baseUrl}/results/${analysisId}`, {
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const data: AnalysisResult = await response.json();

        if (data.status === 'done') {
          setResult(data);
          setStatus('done');
          clearInterval(interval);
        } else if (data.status === 'error') {
          setError(data.error || "L'analyse a échoué.");
          setStatus('error');
          clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.message || "Erreur lors de la vérification du statut.");
        setStatus('error');
        clearInterval(interval);
      }
    }, 2500); // Polling toutes les 2.5 secondes

    return () => clearInterval(interval);
  }, [analysisId, baseUrl]);

  return { result, status, error };
};