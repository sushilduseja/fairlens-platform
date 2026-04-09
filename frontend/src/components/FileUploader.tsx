import { useState, useRef } from "react";

type Props = {
  onFileSelected: (file: File, headers: string[]) => void;
};

export function FileUploader({ onFileSelected }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function processFile(file: File | undefined) {
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files supported.");
      return;
    }
    
    const text = await file.text();
    const firstLine = text.split(/\r?\n/, 1)[0] ?? "";
    const headers = firstLine.split(",").map((h) => h.trim()).filter(Boolean);
    
    if (headers.length === 0) {
      setError("CSV header row missing.");
      return;
    }
    
    setError(null);
    onFileSelected(file, headers);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    processFile(e.dataTransfer.files[0]);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  return (
    <div className="file-uploader">
      <div 
        className={`upload-zone ${isDragging ? "dragging" : ""} animate-in`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
      >
        <input 
          ref={inputRef}
          type="file" 
          accept=".csv" 
          onChange={(e) => processFile(e.target.files?.[0])} 
          hidden
        />
        <div className="upload-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <p className="upload-text">
          <strong>Click to upload</strong> or drag and drop
        </p>
        <p className="upload-hint">CSV files up to 500MB</p>
      </div>
      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}
