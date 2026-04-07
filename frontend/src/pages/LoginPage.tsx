import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiFetch } from "../hooks/useApi";

type LoginResponse = {
  session_token: string;
  user: { id: string; email: string; name: string };
};

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await apiFetch<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setError(null);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <div className="auth-shell">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>Login</h1>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Login</button>
        <p>
          New here? <Link to="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}
