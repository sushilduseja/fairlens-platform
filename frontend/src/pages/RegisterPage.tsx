import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../hooks/useApi";

type RegisterResponse = {
  user_id: string;
  api_key: string;
};

export function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setIsLoading(true);
    try {
      const response = await apiFetch<RegisterResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      localStorage.setItem("fairlens_api_key", response.api_key);
      setApiKey(response.api_key);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  }

  function copyToClipboard() {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="auth-logo">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M9 12l2 2 4-4"/>
            </svg>
          </div>
          <h1>Create Account</h1>
          <p>Start auditing your ML models for fairness</p>
        </div>

        {apiKey ? (
          <div className="auth-success">
            <div className="success-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                <path d="M22 4L12 14.01l-3-3"/>
              </svg>
            </div>
            <h2>Account Created!</h2>
            <p>Your API key has been generated. Save this securely — it won't be shown again.</p>
            
            <div className="api-key-display">
              <code>{apiKey}</code>
              <button onClick={copyToClipboard} className="copy-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                </svg>
              </button>
            </div>
            
            <Link to="/" className="btn-primary btn-full">
              Go to Dashboard
            </Link>
          </div>
        ) : (
          <form className="auth-form" onSubmit={onSubmit}>
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input 
                id="name"
                type="text" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                placeholder="Jane Smith"
                required 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input 
                id="email"
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                placeholder="jane@company.com"
                required 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input 
                id="password"
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                placeholder="Minimum 8 characters"
                minLength={8} 
                required 
              />
            </div>
            
            {error && <div className="form-error">{error}</div>}
            
            <button type="submit" className="btn-primary btn-full" disabled={isLoading}>
              {isLoading ? "Creating Account..." : "Create Account"}
            </button>
            
            <p className="auth-footer">
              Already registered? <Link to="/login">Sign in</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
