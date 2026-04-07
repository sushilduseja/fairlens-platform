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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [step, setStep] = useState(1);

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
    if (modelId) return modelId;
    if (!newModelName) throw new Error("Select existing model or enter new model name.");
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

    setIsSubmitting(true);
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
      setIsSubmitting(false);
    }
  }

  const canProceedToStep2 = file && headers.length > 0;
  const canProceedToStep3 = attributes.filter(a => a.name && a.privileged_group && a.unprivileged_group).length > 0;
  const canSubmit = canProceedToStep2 && canProceedToStep3 && selectedMetrics.length > 0 && (modelId || newModelName);

  return (
    <section className="new-audit">
      <div className="new-audit-header">
        <h2>New Audit</h2>
        <p>Configure and run a fairness audit on your model predictions.</p>
      </div>

      {/* Step Indicator */}
      <div className="step-indicator">
        <div className={`step ${step >= 1 ? "active" : ""} ${step > 1 ? "completed" : ""}`}>
          <span className="step-number">1</span>
          <span className="step-label">Model & Data</span>
        </div>
        <div className="step-line"></div>
        <div className={`step ${step >= 2 ? "active" : ""} ${step > 2 ? "completed" : ""}`}>
          <span className="step-number">2</span>
          <span className="step-label">Attributes</span>
        </div>
        <div className="step-line"></div>
        <div className={`step ${step >= 3 ? "active" : ""}`}>
          <span className="step-number">3</span>
          <span className="step-label">Metrics</span>
        </div>
      </div>

      <form className="new-audit-form" onSubmit={onSubmit}>
        {/* Step 1: Model & Data */}
        <div className={`form-step ${step === 1 ? "active" : "inactive"}`}>
          <div className="step-content">
            <div className="card">
              <h3>
                <span className="step-icon">1</span>
                Select Model
              </h3>
              <label>
                Existing model
                <select value={modelId} onChange={(e) => { setModelId(e.target.value); setNewModelName(""); }}>
                  <option value="">Create new model</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>{model.name}</option>
                  ))}
                </select>
              </label>
              {!modelId && (
                <>
                  <label>
                    New model name
                    <input 
                      value={newModelName} 
                      onChange={(e) => setNewModelName(e.target.value)} 
                      placeholder="e.g., Credit Scoring v3.1"
                    />
                  </label>
                  <label>
                    Use case
                    <select value={newModelUseCase} onChange={(e) => setNewModelUseCase(e.target.value)}>
                      <option value="credit_approval">Credit Approval</option>
                      <option value="fraud_detection">Fraud Detection</option>
                      <option value="underwriting">Underwriting</option>
                      <option value="insurance">Insurance</option>
                      <option value="other">Other</option>
                    </select>
                  </label>
                </>
              )}
            </div>

            <div className="card">
              <h3>
                <span className="step-icon">2</span>
                Upload Data
              </h3>
              <FileUploader onFileSelected={onFileSelected} />
              
              {file && headers.length > 0 && (
                <div className="file-preview">
                  <div className="file-info">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
                    </svg>
                    <span>{file.name}</span>
                    <span className="column-count">{headers.length} columns</span>
                  </div>
                </div>
              )}
            </div>

            {file && headers.length > 0 && (
              <div className="card">
                <h3>
                  <span className="step-icon">3</span>
                  Column Mapping
                </h3>
                <div className="column-mapper">
                  <label>
                    Prediction column
                    <select value={predictionColumn} onChange={(e) => setPredictionColumn(e.target.value)}>
                      {headers.map((header) => (
                        <option key={header} value={header}>{header}</option>
                      ))}
                    </select>
                    <span className="field-hint">Column containing model predictions (0-1 scores)</span>
                  </label>
                  <label>
                    Ground truth column (optional)
                    <select value={groundTruthColumn} onChange={(e) => setGroundTruthColumn(e.target.value)}>
                      <option value="">Not provided</option>
                      {headers.map((header) => (
                        <option key={header} value={header}>{header}</option>
                      ))}
                    </select>
                    <span className="field-hint">Actual labels for metrics requiring ground truth</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          <div className="step-actions">
            <button 
              type="button" 
              className="btn-primary" 
              disabled={!canProceedToStep2}
              onClick={() => setStep(2)}
            >
              Continue to Attributes
            </button>
          </div>
        </div>

        {/* Step 2: Protected Attributes */}
        <div className={`form-step ${step === 2 ? "active" : "inactive"}`}>
          <div className="step-content">
            <div className="card">
              <h3>Protected Attributes</h3>
              <p className="step-description">Define the demographic attributes to test for fairness.</p>
              
              <div className="attributes-list">
                {attributes.map((attribute, index) => (
                  <div key={index} className="attribute-config">
                    <div className="attribute-field">
                      <label>Column</label>
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
                    </div>
                    <div className="attribute-field">
                      <label>Privileged Group</label>
                      <input
                        placeholder="e.g., Male"
                        value={attribute.privileged_group}
                        onChange={(e) => {
                          const next = [...attributes];
                          next[index].privileged_group = e.target.value;
                          setAttributes(next);
                        }}
                      />
                    </div>
                    <div className="attribute-field">
                      <label>Unprivileged Group</label>
                      <input
                        placeholder="e.g., Female"
                        value={attribute.unprivileged_group}
                        onChange={(e) => {
                          const next = [...attributes];
                          next[index].unprivileged_group = e.target.value;
                          setAttributes(next);
                        }}
                      />
                    </div>
                    {attributes.length > 1 && (
                      <button 
                        type="button" 
                        className="btn-remove"
                        onClick={() => setAttributes(prev => prev.filter((_, i) => i !== index))}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <button 
                type="button" 
                className="btn-add"
                onClick={() => setAttributes((prev) => [...prev, { name: headers[0] ?? "", type: "categorical", privileged_group: "", unprivileged_group: "" }])}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14"/>
                </svg>
                Add Attribute
              </button>
            </div>
          </div>

          <div className="step-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button 
              type="button" 
              className="btn-primary" 
              disabled={!canProceedToStep3}
              onClick={() => setStep(3)}
            >
              Continue to Metrics
            </button>
          </div>
        </div>

        {/* Step 3: Metrics */}
        <div className={`form-step ${step === 3 ? "active" : "inactive"}`}>
          <div className="step-content">
            <div className="card">
              <h3>Select Metrics</h3>
              <p className="step-description">Choose the fairness metrics to compute.</p>
              
              <div className="metrics-selection">
                {metrics.map((metric) => (
                  <label key={metric.name} className={`metric-option ${selectedMetrics.includes(metric.name) ? "selected" : ""}`}>
                    <input
                      type="checkbox"
                      checked={selectedMetrics.includes(metric.name)}
                      onChange={(e) => {
                        setSelectedMetrics((prev) =>
                          e.target.checked ? [...prev, metric.name] : prev.filter((name) => name !== metric.name)
                        );
                      }}
                    />
                    <div className="metric-content">
                      <span className="metric-name">{metric.display_name}</span>
                      <span className="metric-desc">{metric.description}</span>
                      {metric.requires_ground_truth && (
                        <span className="metric-tag">Requires ground truth</span>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="step-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button 
              type="submit" 
              className="btn-primary btn-submit" 
              disabled={!canSubmit || isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Run Audit"}
            </button>
          </div>
        </div>

        {error && <div className="form-error">{error}</div>}
      </form>
    </section>
  );
}
