import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { FileUploader } from "../components/FileUploader";
import { apiFetch } from "../hooks/useApi";
import type { MetricInfo, ModelCreateResponse } from "../utils/types";

type MetricResponse = { metrics: MetricInfo[] };
type ModelOption = { id: string; name: string };
type ModelListResponse = { models: Array<{ model_id: string; name: string }> };

type AuditCreateResponse = {
  audit_id: string;
  status: string;
  created_at: string;
};

type ProtectedAttribute = {
  name: string;
  type: "binary" | "categorical";
  privileged_group: string;
  unprivileged_group: string;
};

export function NewAuditPage() {
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [predictionColumn, setPredictionColumn] = useState("");
  const [groundTruthColumn, setGroundTruthColumn] = useState("");
  const [metrics, setMetrics] = useState<MetricInfo[]>([]);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(["demographic_parity"]);
  const [attributes, setAttributes] = useState<ProtectedAttribute[]>([]);

  const [models, setModels] = useState<ModelOption[]>([]);
  const [modelId, setModelId] = useState("");
  const [newModelName, setNewModelName] = useState("");
  const [newModelUseCase, setNewModelUseCase] = useState("credit_approval");

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<MetricResponse>("/metrics")
      .then((res) => setMetrics(res.metrics))
      .catch(() => setMetrics([]));

    apiFetch<ModelListResponse>("/models")
      .then((res) => setModels(res.models.map((model) => ({ id: model.model_id, name: model.name }))))
      .catch(() => setModels([]));
  }, []);

  function onFileSelected(selected: File, parsedHeaders: string[]) {
    setFile(selected);
    setHeaders(parsedHeaders);
    if (parsedHeaders.length > 0) {
      setPredictionColumn(parsedHeaders[0]);
      setAttributes([{ name: parsedHeaders[0], type: "categorical", privileged_group: "", unprivileged_group: "" }]);
    }
  }

  async function createModelIfNeeded(): Promise<string> {
    if (modelId) {
      return modelId;
    }
    if (!newModelName) {
      throw new Error("Select existing model or enter new model name.");
    }
    const model = await apiFetch<ModelCreateResponse>("/models", {
      method: "POST",
      body: JSON.stringify({ name: newModelName, use_case: newModelUseCase, description: null }),
    });
    const next = { id: model.model_id, name: model.name };
    setModels((prev) => [next, ...prev]);
    setModelId(next.id);
    return next.id;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Upload CSV first.");
      return;
    }

    try {
      const chosenModelId = await createModelIfNeeded();
      const payload = new FormData();
      payload.set("model_id", chosenModelId);
      payload.set("file", file);
      payload.set("prediction_column", predictionColumn);
      payload.set("ground_truth_column", groundTruthColumn || "");
      payload.set("protected_attributes", JSON.stringify(attributes.filter((a) => a.name)));
      payload.set("selected_metrics", JSON.stringify(selectedMetrics));

      const result = await apiFetch<AuditCreateResponse>("/audits", {
        method: "POST",
        body: payload,
      });

      navigate(`/audits/${result.audit_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit audit");
    }
  }

  return (
    <section>
      <h2>New Audit</h2>
      <form className="audit-form" onSubmit={onSubmit}>
        <div className="card">
          <h3>Model</h3>
          <label>
            Existing model
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              <option value="">Create new</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>{model.name}</option>
              ))}
            </select>
          </label>
          {!modelId ? (
            <>
              <label>
                New model name
                <input value={newModelName} onChange={(e) => setNewModelName(e.target.value)} />
              </label>
              <label>
                Use case
                <select value={newModelUseCase} onChange={(e) => setNewModelUseCase(e.target.value)}>
                  <option value="credit_approval">Credit approval</option>
                  <option value="fraud_detection">Fraud detection</option>
                  <option value="underwriting">Underwriting</option>
                  <option value="insurance">Insurance</option>
                  <option value="other">Other</option>
                </select>
              </label>
            </>
          ) : null}
        </div>

        <FileUploader onFileSelected={onFileSelected} />

        <div className="card">
          <h3>Column Mapping</h3>
          <label>
            Prediction column
            <select value={predictionColumn} onChange={(e) => setPredictionColumn(e.target.value)}>
              {headers.map((header) => (
                <option key={header} value={header}>{header}</option>
              ))}
            </select>
          </label>
          <label>
            Ground truth column (optional)
            <select value={groundTruthColumn} onChange={(e) => setGroundTruthColumn(e.target.value)}>
              <option value="">Not provided</option>
              {headers.map((header) => (
                <option key={header} value={header}>{header}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="card">
          <h3>Protected Attributes</h3>
          {attributes.map((attribute, index) => (
            <div key={index} className="attribute-row">
              <select
                value={attribute.name}
                onChange={(e) => {
                  const next = [...attributes];
                  next[index].name = e.target.value;
                  setAttributes(next);
                }}
              >
                {headers.map((header) => (
                  <option key={header} value={header}>{header}</option>
                ))}
              </select>
              <input
                placeholder="Privileged group"
                value={attribute.privileged_group}
                onChange={(e) => {
                  const next = [...attributes];
                  next[index].privileged_group = e.target.value;
                  setAttributes(next);
                }}
              />
              <input
                placeholder="Unprivileged group"
                value={attribute.unprivileged_group}
                onChange={(e) => {
                  const next = [...attributes];
                  next[index].unprivileged_group = e.target.value;
                  setAttributes(next);
                }}
              />
            </div>
          ))}
          <button
            type="button"
            onClick={() => setAttributes((prev) => [...prev, { name: headers[0] ?? "", type: "categorical", privileged_group: "", unprivileged_group: "" }])}
          >
            Add Attribute
          </button>
        </div>

        <div className="card">
          <h3>Metrics</h3>
          <div className="metric-checks">
            {metrics.map((metric) => (
              <label key={metric.name}>
                <input
                  type="checkbox"
                  checked={selectedMetrics.includes(metric.name)}
                  onChange={(e) => {
                    setSelectedMetrics((prev) =>
                      e.target.checked ? [...prev, metric.name] : prev.filter((name) => name !== metric.name)
                    );
                  }}
                />
                <span>{metric.display_name}</span>
                <small>{metric.description}</small>
              </label>
            ))}
          </div>
        </div>

        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Submit Audit</button>
      </form>
    </section>
  );
}
