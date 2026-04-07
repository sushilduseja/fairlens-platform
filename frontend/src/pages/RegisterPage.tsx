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

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
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
    }
  }

  return (
    <div className="auth-shell">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>Register</h1>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" minLength={8} required />
        </label>
        {error ? <p className="error">{error}</p> : null}
        {apiKey ? (
          <div className="ok-box">
            <strong>API Key</strong>
            <code>{apiKey}</code>
          </div>
        ) : null}
        <button type="submit">Create Account</button>
        <p>
          Already registered? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}
