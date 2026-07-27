import { useDropzone } from "react-dropzone";
import { CloudArrowUpIcon } from "@heroicons/react/24/outline";

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