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
    
    if (modelNameInvalid) {
      setError("Please enter a model name.");
      return;
    }
    
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
  const modelNameInvalid = newModelName.trim() === "" && !modelId;
  const canProceedToStep3 = attributes.filter(a => a.name && a.privileged_group && a.unprivileged_group).length > 0;
  const canSubmit = canProceedToStep2 && canProceedToStep3 && selectedMetrics.length > 0 && (modelId || newModelName) && !modelNameInvalid;

  return (
    <section className="new-audit">
      <div className="new-audit-header animate-in">
        <h2>New Audit</h2>
        <p>Configure and run a fairness audit on your model predictions.</p>
      </div>

      {/* Configuration Progress */}
      <div className="config-progress animate-in" style={{animationDelay: "50ms"}}>
        <div className="progress-track">
          <div className={`progress-step ${step >= 1 ? "active" : ""}`} data-step="1">
            <span className="step-label">Model & Data</span>
          </div>
          <div className="progress-line">
            <div className={`line-fill ${step >= 2 ? "filled" : ""}`}></div>
          </div>
          <div className={`progress-step ${step >= 2 ? "active" : ""}`} data-step="2">
            <span className="step-label">Attributes</span>
          </div>
          <div className="progress-line">
            <div className={`line-fill ${step >= 3 ? "filled" : ""}`}></div>
          </div>
          <div className={`progress-step ${step >= 3 ? "active" : ""}`} data-step="3">
            <span className="step-label">Metrics</span>
          </div>
        </div>
      </div>

      <form className="new-audit-form" onSubmit={onSubmit}>
         {/* Step 1: Model & Data Configuration */}
         <div className={`form-step ${step === 1 ? "active" : "inactive"}`}>
           <div className="config-panel">
             <div className="config-section">
               <div className="section-header">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                   <path d="M20 7if 2 2 0 00-2-2H6a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V7z"/>
                   <path d="M12 11v6M9 14h6"/>
                 </svg>
                 <h3>Model Identity</h3>
               </div>
               <div className="config-grid">
                 <div className="config-group">
                   <label>Target Model</label>
                   <select value={modelId} onChange={(e) => { setModelId(e.target.value); setNewModelName(""); }}>
                     <option value="">Define new model</option>
                     {models.map((model) => (
                       <option key={model.id} value={model.id}>{model.name}</option>
                     ))}
                   </select>
                 </div>
                 {!modelId && (
                   <div className="config-sub-group">
                     <div className="config-group">
                       <label>Model Name</label>
                       <input 
                         value={newModelName} 
                         onChange={(e) => setNewModelName(e.target.value)} 
                         placeholder="e.g., Credit Scoring v3.1"
                         className={newModelName.trim() === "" && newModelName.length > 0 ? "input-error" : ""}
                       />
                       {newModelName.trim() === "" && newModelName.length > 0 && <span className="field-error">Model name is required</span>}
                     </div>
                     <div className="config-group">
                       <label>Application Use Case</label>
                       <select value={newModelUseCase} onChange={(e) => setNewModelUseCase(e.target.value)}>
                         <option value="credit_approval">Credit Approval</option>
                         <option value="fraud_detection">Fraud Detection</option>
                         <option value="underwriting">Underwriting</option>
                         <option value="insurance">Insurance</option>
                         <option value="other">Other</option>
                       </select>
                     </div>
                   </div>
                 )}
               </div>
             </div>
 
             <div className="config-section">
               <div className="section-header">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                   <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                 </svg>
                 <h3>Dataset Source</h3>
               </div>
               <div className="upload-zone-container">
                 <FileUploader onFileSelected={onFileSelected} />
                 {file && headers.length > 0 && (
                   <div className="file-verified-badge">
                     <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                       <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                       <path d="M22 4L12 14.01l-3-3"/>
                     </svg>
                     <span>{file.name} verified — {headers.length} columns detected</span>
                   </div>
                 )}
               </div>
             </div>
 
             {file && headers.length > 0 && (
               <div className="config-section">
                 <div className="section-header">
                   <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                     <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 113 3L12 15l-4 1 1-4 9.5-9.5z"/>
                   </svg>
                   <h3>Schema Mapping</h3>
                 </div>
                 <div className="mapping-grid">
                   <div className="mapping-item">
                     <label>Prediction Column</label>
                     <div className="mapping-input-wrapper">
                       <select value={predictionColumn} onChange={(e) => setPredictionColumn(e.target.value)}>
                         {headers.map((header) => (
                           <option key={header} value={header}>{header}</option>
                         ))}
                       </select>
                       <span className="mapping-hint">Target continuous variable (0.0 - 1.0)</span>
                     </div>
                   </div>
                   <div className="mapping-item">
                     <label>Ground Truth Column</label>
                     <div className="mapping-input-wrapper">
                       <select value={groundTruthColumn} onChange={(e) => setGroundTruthColumn(e.target.value)}>
                         <option value="">None (Unsupervised)</option>
                         {headers.map((header) => (
                           <option key={header} value={header}>{header}</option>
                         ))}
                       </select>
                       <span className="mapping-hint">Actual outcomes for performance-based metrics</span>
                     </div>
                   </div>
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
               Continue to Attribute Configuration
             </button>
           </div>
         </div>


         {/* Step 2: Protected Attribute Configuration */}
         <div className={`form-step ${step === 2 ? "active" : "inactive"}`}>
           <div className="config-panel">
             <div className="config-section">
               <div className="section-header">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                   <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                   <circle cx="9" cy="7" r="4"/>
                   <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
                 </svg>
                 <h3>Protected Attributes</h3>
               </div>
               <p className="section-description">Define the demographic dimensions to test for disparity. FairLens will compare the privileged group against the unprivileged group for each attribute.</p>
               
               <div className="attributes-grid">
                 {attributes.map((attribute, index) => (
                   <div key={index} className="attribute-row">
                     <div className="attribute-col">
                       <label>Attribute Column</label>
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
                     <div className="attribute-col">
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
                     <div className="attribute-col">
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
                     <div className="attribute-action">
                       {attributes.length > 1 && (
                         <button 
                           type="button" 
                           className="btn-remove-attr"
                           onClick={() => setAttributes(prev => prev.filter((_, i) => i !== index))}
                         >
                           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                             <path d="M18 6L6 18M6 6l12 12"/>
                           </svg>
                         </button>
                       )}
                     </div>
                   </div>
                 ))}
               </div>
 
               <button 
                 type="button" 
                 className="btn-add-attr"
                 onClick={() => setAttributes((prev) => [...prev, { name: headers[0] ?? "", type: "categorical", privileged_group: "", unprivileged_group: "" }])}
               >
                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                   <path d="M12 5v14M5 12h14"/>
                 </svg>
                 Add Dimension
               </button>
             </div>
           </div>
 
           <div className="step-actions">
             <button type="button" className="btn-secondary" onClick={() => setStep(1)}>Previous Step</button>
             <button 
               type="button" 
               className="btn-primary" 
               disabled={!canProceedToStep3}
               onClick={() => setStep(3)}
             >
               Continue to Metrics Selection
             </button>
           </div>
         </div>


         {/* Step 3: Fairness Metrics Selection */}
         <div className={`form-step ${step === 3 ? "active" : "inactive"}`}>
           <div className="config-panel">
             <div className="config-section">
               <div className="section-header">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                   <path d="M21.21 15.89A10 10 0 118 2.83"/>
                   <path d="M22 12A10 10 0 0012 2v10z"/>
                 </svg>
                 <h3>Fairness Metrics</h3>
               </div>
               <p className="section-description">Select the statistical metrics to apply. Metrics marked with "Ground Truth" require a target label column to be calculated.</p>
               
               <div className="metrics-grid animate-in-stagger">
                 {metrics.map((metric) => (
                   <label key={metric.name} className={`metric-card ${selectedMetrics.includes(metric.name) ? "selected" : ""}`}>
                     <div className="metric-checkbox">
                       <input
                         type="checkbox"
                         checked={selectedMetrics.includes(metric.name)}
                         onChange={(e) => {
                           setSelectedMetrics((prev) =>
                             e.target.checked ? [...prev, metric.name] : prev.filter((name) => name !== metric.name)
                           );
                         }}
                       />
                     </div>
                     <div className="metric-details">
                       <div className="metric-header">
                         <span className="metric-title">{metric.display_name}</span>
                         {metric.requires_ground_truth && (
                           <span className="metric-requirement">Ground Truth Required</span>
                         )}
                       </div>
                       <span className="metric-description">{metric.description}</span>
                     </div>
                   </label>
                 ))}
               </div>
             </div>
           </div>
 
           <div className="step-actions">
             <button type="button" className="btn-secondary" onClick={() => setStep(2)}>Previous Step</button>
             <button 
               type="submit" 
               className="btn-primary btn-submit" 
               disabled={!canSubmit || isSubmitting}
             >
               {isSubmitting ? (
                 <div className="btn-loading">
                   <div className="spinner-sm"></div>
                   Submitting...
                 </div>
               ) : "Initialize Fairness Audit"}
             </button>
           </div>
         </div>


        {error && <div className="form-error">{error}</div>}
      </form>
    </section>
  );
}
