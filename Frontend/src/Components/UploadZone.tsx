import { useDropzone } from "react-dropzone";

const CloudArrowUpIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
  </svg>
);

export const UploadZone = ({ onUpload, isLoading }: { onUpload: (file: File) => void; isLoading: boolean }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"], "application/vnd.ms-excel": [".xlsx", ".xls"] },
    onDrop: (files) => !isLoading && onUpload(files[0]),
    disabled: isLoading,
  });

  return (
    <div
      {...getRootProps()}
      className={`card rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
        isLoading
          ? "border-gray-600 opacity-50"
          : isDragActive
          ? "border-cyan-400 bg-cyan-500/10 shadow-glow scale-[1.01]"
          : "border-cyan-500/20 hover:border-cyan-400/60 hover:shadow-glow"
      }`}
    >
      <input {...getInputProps()} />
      <div className={`w-20 h-20 mx-auto mb-5 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center ${isDragActive ? "animate-bounce" : "animate-float"}`}>
        <CloudArrowUpIcon className="w-10 h-10 text-cyan-400" />
      </div>
      <p className="text-lg font-semibold text-white">
        {isDragActive ? "Relâchez pour analyser" : "Déposez votre fichier financier"}
      </p>
      <p className="text-gray-400 text-sm mt-2">ou cliquez pour parcourir — CSV, XLSX, XLS</p>
      <p className="text-gray-600 text-xs mt-3">Vos données sont analysées par nos agents IA</p>
      {isLoading && (
        <div className="mt-5 inline-flex items-center gap-2 text-cyan-400 text-sm">
          <svg className="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          Analyse en cours...
        </div>
      )}
    </div>
  );
};
