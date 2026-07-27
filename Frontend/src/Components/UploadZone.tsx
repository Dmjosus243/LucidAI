import { useDropzone } from "react-dropzone";

const CloudArrowUpIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
  </svg>
);

export const UploadZone = ({ onUpload, isLoading }: { onUpload: (file: File) => void; isLoading: boolean }) => {
  const { getRootProps, getInputProps } = useDropzone({
    accept: { "text/csv": [".csv"], "application/vnd.ms-excel": [".xlsx", ".xls"] },
    onDrop: (files) => !isLoading && onUpload(files[0]),
    disabled: isLoading,
  });

  return (
    <div
      {...getRootProps()}
      className={`glass rounded-2xl p-12 text-center cursor-pointer transition-all hover:border-cyan-500 border-2 border-dashed ${
        isLoading ? "border-gray-600 opacity-50" : "border-gray-700"
      }`}
    >
      <input {...getInputProps()} />
      <CloudArrowUpIcon className="w-16 h-16 text-cyan-400 mx-auto mb-4" />
      <p className="text-lg font-medium text-white">Déposez votre fichier financier</p>
      <p className="text-gray-400 text-sm mt-2">CSV ou Excel (XLSX, XLS)</p>
      {isLoading && <div className="mt-4 text-cyan-400">Analyse en cours...</div>}
    </div>
  );
};