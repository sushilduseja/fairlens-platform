import { useState } from "react";

type Props = {
  onFileSelected: (file: File, headers: string[]) => void;
};

export function FileUploader({ onFileSelected }: Props) {
  const [error, setError] = useState<string | null>(null);

  async function onChange(file: File | undefined) {
    if (!file) {
      return;
    }
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

  return (
    <div className="card">
      <label className="field-label" htmlFor="csv-file">CSV Upload</label>
      <input id="csv-file" type="file" accept=".csv" onChange={(e) => onChange(e.target.files?.[0])} />
      <p className="field-hint">Max 500MB. Header row required.</p>
      {error ? <p className="error">{error}</p> : null}
    </div>
  );
}
