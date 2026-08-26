import React, { useState } from "react";
import { api } from "../api.js";

export default function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [grade, setGrade] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = mode === "login"
        ? await api.login(name, password)
        : await api.register(name, grade, password);
      localStorage.setItem("ai_tutor_token", result.token);
      onAuthenticated(result.student);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand"><span className="brand-mark">∞</span><span className="brand-name">Learnflix</span></div>
        <span className="eyebrow">Private learning space</span>
        <h1>{mode === "login" ? "Welcome back" : "Create your learner account"}</h1>
        <p className="auth-copy">Your progress and learning history stay tied to your account.</p>
        <form className="auth-form" onSubmit={submit}>
          <label>Student name<input required value={name} onChange={(event) => setName(event.target.value)} autoComplete="username" /></label>
          {mode === "register" && <label>Grade <span className="auth-optional">optional</span><input value={grade} onChange={(event) => setGrade(event.target.value)} /></label>}
          <label>Password<input required minLength="8" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
          {error && <div className="banner banner-error">{error}</div>}
          <button className="btn btn-primary auth-submit" disabled={busy}>{busy ? "Opening..." : mode === "login" ? "Log in" : "Create account"}</button>
        </form>
        <button className="auth-toggle" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}>{mode === "login" ? "New student? Create an account" : "Already have an account? Log in"}</button>
      </section>
    </main>
  );
}
