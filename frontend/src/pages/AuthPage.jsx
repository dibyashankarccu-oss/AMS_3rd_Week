import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth } from "../utils/auth";

export default function AuthPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate();

  function handleSubmit() {
    setError(null);
    setSuccess(null);

    if (!email || !password || (isRegister && !name)) {
      setError("All fields are required");
      return;
    }

    if (isRegister) {
      const user = auth.register(email, password, name);
      if (!user) {
        setError("User already exists");
        return;
      }
      setSuccess("Registration successful! Please login.");
      setIsRegister(false);
      return;
    }

    const user = auth.login(email, password);
    if (!user) {
      setError("Invalid credentials");
      return;
    }

    navigate("/search", { replace: true });
  }

  const features = [
    {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      ),
      title: "Real-Time Incident Tracking",
      desc: "Detect, log, and escalate incidents the moment they occur with automated severity classification.",
    },
    {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      ),
      title: "Structured SLA Compliance",
      desc: "Define response and resolution SLAs per ticket priority. Automated reminders keep teams accountable.",
    },
    {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      ),
      title: "Unified Analytics Dashboard",
      desc: "Get operational visibility with live charts on ticket volumes, resolution times, and team performance.",
    }
  ];

  const stats = [
    { value: "99.9%", label: "Uptime SLA" },
    { value: "< 2min", label: "Avg. Response" },
    { value: "500+", label: "Incidents Resolved" },
  ];

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .auth-root {
          min-height: 100vh;
          display: flex;
          background: #07090f;
        }

        /* ── LEFT PANEL ─────────────────────────────────── */
        .auth-left {
          flex: 1 1 0;
          min-height: 100vh;
          position: relative;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          padding: 3rem 3.5rem;
          background: linear-gradient(145deg, #0a0d1a 0%, #070a16 60%, #0e0820 100%);
        }

        .auth-left-noise {
          position: absolute;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.025'/%3E%3C/svg%3E");
          pointer-events: none;
          opacity: 0.6;
        }

        .auth-left-glow1 {
          position: absolute;
          top: -100px;
          left: -100px;
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(109, 40, 217, 0.12) 0%, transparent 65%);
          pointer-events: none;
        }
        .auth-left-glow2 {
          position: absolute;
          bottom: -80px;
          right: -80px;
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(37, 99, 235, 0.1) 0%, transparent 65%);
          pointer-events: none;
        }
        .auth-left-glow3 {
          position: absolute;
          top: 45%;
          left: 30%;
          width: 300px;
          height: 300px;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.06) 0%, transparent 70%);
          pointer-events: none;
        }

        /* Grid lines */
        .auth-left-grid {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(139, 92, 246, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 92, 246, 0.04) 1px, transparent 1px);
          background-size: 48px 48px;
          pointer-events: none;
        }

        .auth-left-content {
          position: relative;
          z-index: 2;
          display: flex;
          flex-direction: column;
          height: 100%;
        }

        /* Brand */
        .auth-brand {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: auto;
        }
        .auth-brand-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          background: linear-gradient(135deg, #7c3aed, #2563eb);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4);
          flex-shrink: 0;
        }
        .auth-brand-name {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          font-size: 1.3rem;
          color: #fff;
          letter-spacing: -0.02em;
        }
        .auth-brand-name span { color: #a78bfa; }

        /* Hero text */
        .auth-hero {
          margin-top: 3.5rem;
          margin-bottom: 2.5rem;
        }
        .auth-hero-eyebrow {
          font-size: 0.7rem;
          font-weight: 500;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #7c3aed;
          background: rgba(124, 58, 237, 0.1);
          border: 1px solid rgba(124, 58, 237, 0.2);
          display: inline-block;
          padding: 0.3rem 0.75rem;
          border-radius: 100px;
          margin-bottom: 1.25rem;
        }
        .auth-hero-title {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          font-size: clamp(1.75rem, 2.5vw, 2.6rem);
          line-height: 1.12;
          color: #f1f5f9;
          letter-spacing: -0.03em;
          margin-bottom: 1rem;
        }
        .auth-hero-title em {
          font-style: normal;
          background: linear-gradient(90deg, #a78bfa, #60a5fa);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .auth-hero-sub {
          font-size: 0.9rem;
          color: #64748b;
          line-height: 1.7;
          max-width: 380px;
          font-weight: 400;
        }

        /* Features */
        .auth-features {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-bottom: 2.5rem;
        }
        .auth-feature {
          display: flex;
          align-items: flex-start;
          gap: 0.875rem;
          padding: 0.9rem 1rem;
          border-radius: 14px;
          border: 1px solid rgba(139, 92, 246, 0.08);
          background: rgba(139, 92, 246, 0.035);
          transition: border-color 0.2s;
        }
        .auth-feature:hover {
          border-color: rgba(139, 92, 246, 0.18);
          background: rgba(139, 92, 246, 0.06);
        }
        .auth-feature-icon {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          background: rgba(124, 58, 237, 0.12);
          border: 1px solid rgba(139, 92, 246, 0.18);
          color: #a78bfa;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .auth-feature-title {
          font-size: 0.85rem;
          font-weight: 600;
          color: #cbd5e1;
          margin-bottom: 0.2rem;
          font-family: 'Syne', sans-serif;
          letter-spacing: -0.01em;
        }
        .auth-feature-desc {
          font-size: 0.75rem;
          color: #475569;
          line-height: 1.55;
        }

        /* Stats bar */
        .auth-stats {
          display: flex;
          gap: 0;
          border: 1px solid rgba(139, 92, 246, 0.1);
          border-radius: 14px;
          overflow: hidden;
          background: rgba(255,255,255,0.015);
        }
        .auth-stat {
          flex: 1;
          padding: 0.9rem 1rem;
          text-align: center;
          border-right: 1px solid rgba(139, 92, 246, 0.08);
        }
        .auth-stat:last-child { border-right: none; }
        .auth-stat-val {
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 1.05rem;
          color: #a78bfa;
          letter-spacing: -0.02em;
        }
        .auth-stat-lbl {
          font-size: 0.65rem;
          color: #475569;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-top: 2px;
        }

        /* ── RIGHT PANEL ─────────────────────────────────── */
        .auth-right {
          width: 480px;
          flex-shrink: 0;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #070910;
          border-left: 1px solid rgba(139, 92, 246, 0.1);
          position: relative;
          overflow: hidden;
        }
        .auth-right::before {
          content: '';
          position: absolute;
          top: -120px;
          right: -120px;
          width: 360px;
          height: 360px;
          background: radial-gradient(circle, rgba(109, 40, 217, 0.07) 0%, transparent 65%);
          pointer-events: none;
        }
        .auth-right::after {
          content: '';
          position: absolute;
          bottom: -80px;
          left: -80px;
          width: 280px;
          height: 280px;
          background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, transparent 65%);
          pointer-events: none;
        }

        .auth-form-wrap {
          position: relative;
          z-index: 2;
          width: 100%;
          max-width: 380px;
          padding: 2rem;
        }

        /* Form card */
        .auth-card {
          background: rgba(15, 20, 36, 0.9);
          border: 1px solid rgba(139, 92, 246, 0.15);
          border-radius: 24px;
          padding: 2.25rem 2rem;
          box-shadow: 0 8px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(139,92,246,0.06) inset;
          backdrop-filter: blur(16px);
        }

        .auth-card-eyebrow {
          font-size: 0.65rem;
          font-weight: 600;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: #7c3aed;
          margin-bottom: 0.35rem;
        }
        .auth-card-title {
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 1.5rem;
          color: #f1f5f9;
          letter-spacing: -0.02em;
          margin-bottom: 0.35rem;
        }
        .auth-card-sub {
          font-size: 0.8rem;
          color: #475569;
          margin-bottom: 1.75rem;
        }

        /* Input group */
        .auth-field { margin-bottom: 1rem; }
        .auth-label {
          display: block;
          font-size: 0.68rem;
          font-weight: 600;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: #94a3b8;
          margin-bottom: 0.5rem;
        }
        .auth-input-wrap { position: relative; }
        .auth-input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: #475569;
          pointer-events: none;
        }
        .auth-input {
          width: 100%;
          padding: 0.8rem 1rem 0.8rem 2.75rem;
          background: rgba(7, 9, 16, 0.8);
          border: 1px solid rgba(71, 85, 105, 0.4);
          border-radius: 12px;
          color: #e2e8f0;
          font-size: 0.875rem;
          font-family: 'DM Sans', sans-serif;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .auth-input::placeholder { color: #334155; }
        .auth-input:focus {
          border-color: rgba(139, 92, 246, 0.5);
          box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
        }

        /* Alert */
        .auth-alert {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.7rem 0.875rem;
          border-radius: 10px;
          font-size: 0.8rem;
          margin-bottom: 1rem;
        }
        .auth-alert.error {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: #f87171;
        }
        .auth-alert.success {
          background: rgba(34, 197, 94, 0.08);
          border: 1px solid rgba(34, 197, 94, 0.2);
          color: #4ade80;
        }

        /* Submit button */
        .auth-submit {
          width: 100%;
          padding: 0.875rem;
          border-radius: 12px;
          border: none;
          background: linear-gradient(135deg, #7c3aed, #2563eb);
          color: #fff;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 0.9rem;
          letter-spacing: 0.02em;
          cursor: pointer;
          box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3);
          transition: all 0.2s ease;
          margin-bottom: 1.25rem;
        }
        .auth-submit:hover {
          box-shadow: 0 6px 28px rgba(124, 58, 237, 0.45);
          transform: translateY(-1px);
        }
        .auth-submit:active { transform: translateY(0); }

        /* Toggle link */
        .auth-toggle {
          text-align: center;
          padding-top: 1rem;
          border-top: 1px solid rgba(71, 85, 105, 0.2);
          font-size: 0.8rem;
          color: #475569;
        }
        .auth-toggle button {
          background: none;
          border: none;
          cursor: pointer;
          font-family: 'DM Sans', sans-serif;
        }
        .auth-toggle-link {
          color: #a78bfa;
          font-weight: 600;
          font-family: 'Syne', sans-serif;
          font-size: 0.8rem;
        }

        /* Test creds */
        .auth-creds {
          margin-top: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.6rem 0.875rem;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(71, 85, 105, 0.25);
          border-radius: 100px;
          font-size: 0.7rem;
          color: #475569;
        }
        .auth-creds-val { color: #a78bfa; font-family: monospace; font-size: 0.72rem; }

        /* ── Responsive ─── */
        @media (max-width: 900px) {
          .auth-left { display: none; }
          .auth-right {
            width: 100%;
            border-left: none;
            background: linear-gradient(145deg, #0a0d1a 0%, #07090f 100%);
          }
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }
        .anim-up { animation: slideUp 0.5s ease both; }
        .anim-shake { animation: shake 0.3s ease; }
      `}</style>

      <div className="auth-root">

        {/* ── LEFT: Marketing panel ────────────────────────── */}
        <div className="auth-left">
          <div className="auth-left-noise" />
          <div className="auth-left-grid" />
          <div className="auth-left-glow1" />
          <div className="auth-left-glow2" />
          <div className="auth-left-glow3" />

          <div className="auth-left-content">

            {/* Brand */}
            <div className="auth-brand">
              <div className="auth-brand-icon">
                <svg style={{ width: 22, height: 22 }} fill="none" stroke="white" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <span className="auth-brand-name">AMS <span>Nexus</span></span>
            </div>

            {/* Hero */}
            <div className="auth-hero">
              <div className="auth-hero-eyebrow">Incident Management Platform</div>
              <h1 className="auth-hero-title">
                Resolve incidents<br />
                faster with <em>complete</em><br />
                operational control
              </h1>
              <p className="auth-hero-sub">
                AMS Nexus brings your entire incident lifecycle — from detection to resolution — into a single, structured workspace built for modern operations teams.
              </p>
            </div>

            {/* Features */}
            <div className="auth-features">
              {features.map((f, i) => (
                <div className="auth-feature" key={i}>
                  <div className="auth-feature-icon">{f.icon}</div>
                  <div>
                    <div className="auth-feature-title">{f.title}</div>
                    <div className="auth-feature-desc">{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Stats */}
            <div className="auth-stats">
              {stats.map((s, i) => (
                <div className="auth-stat" key={i}>
                  <div className="auth-stat-val">{s.value}</div>
                  <div className="auth-stat-lbl">{s.label}</div>
                </div>
              ))}
            </div>

          </div>
        </div>

        {/* ── RIGHT: Auth form ─────────────────────────────── */}
        <div className="auth-right">
          <div className="auth-form-wrap anim-up">

            <div className="auth-card">
              <div className="auth-card-eyebrow">Secure Access</div>
              <h2 className="auth-card-title">
                {isRegister ? "Create Account" : "Welcome Back"}
              </h2>
              <p className="auth-card-sub">
                {isRegister
                  ? "Join the AMS Nexus ecosystem"
                  : "Sign in to continue to your dashboard"}
              </p>

              {/* Name (register only) */}
              {isRegister && (
                <div className="auth-field">
                  <label className="auth-label">Full Name</label>
                  <div className="auth-input-wrap">
                    <span className="auth-input-icon">
                      <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </span>
                    <input
                      className="auth-input"
                      placeholder="Enter your full name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                </div>
              )}

              {/* Email */}
              <div className="auth-field">
                <label className="auth-label">Email Address</label>
                <div className="auth-input-wrap">
                  <span className="auth-input-icon">
                    <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </span>
                  <input
                    type="email"
                    className="auth-input"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="auth-field">
                <label className="auth-label">Password</label>
                <div className="auth-input-wrap">
                  <span className="auth-input-icon">
                    <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </span>
                  <input
                    type="password"
                    className="auth-input"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="auth-alert error anim-shake">
                  <svg style={{ width: 15, height: 15, flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </div>
              )}

              {/* Success */}
              {success && (
                <div className="auth-alert success">
                  <svg style={{ width: 15, height: 15, flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {success}
                </div>
              )}

              {/* Submit */}
              <button className="auth-submit" onClick={handleSubmit}>
                {isRegister ? "Create Account" : "Sign In →"}
              </button>

              {/* Toggle */}
              <div className="auth-toggle">
                <button onClick={() => { setIsRegister(!isRegister); setError(null); setSuccess(null); }}>
                  {isRegister ? (
                    <span style={{ color: "#475569" }}>Already have an account? <span className="auth-toggle-link">Sign In</span></span>
                  ) : (
                    <span style={{ color: "#475569" }}>Don't have an account? <span className="auth-toggle-link">Create One</span></span>
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}