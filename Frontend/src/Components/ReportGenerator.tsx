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
    <button
      onClick={handleDownload}
      className="w-full mt-4 bg-cyan-500 hover:bg-cyan-600 text-dark font-bold py-3 rounded-xl transition-colors"
    >
      📄 Télécharger le rapport PDF
    </button>
  );
};