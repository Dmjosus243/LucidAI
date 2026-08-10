import { downloadReport } from "../Services/api";

export const ReportGenerator = ({ analysisId }: { analysisId: string }) => {
  const handleDownload = async () => {
    try {
      const res = await downloadReport(analysisId);
      const url = URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `lucidai_audit_${analysisId}.pdf`;
      link.click();
    } catch (e) {
      alert("Erreur lors du téléchargement du rapport.");
    }
  };

  return (
    <button onClick={handleDownload} className="btn-primary w-full mt-4">
      <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Télécharger le rapport PDF
    </button>
  );
};
