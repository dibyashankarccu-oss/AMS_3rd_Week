import { useState } from "react";
import { apiRequest } from "../api/apiClient";
import TicketCard from "../components/TicketCard";
import TicketTimelineModal from "../components/TicketTimelineModal";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [parentKey, setParentKey] = useState("");
  const [redirecting, setRedirecting] = useState(false);
  const [timelineOpen, setTimelineOpen] = useState(false);
  const [timelineKey, setTimelineKey] = useState("");

  function getParentKey(input) {
    const value = input.trim().toUpperCase();
    const match = value.match(/^([A-Z]+-\d+)/);
    return match ? match[1] : value;
  }

  async function handleSearch() {
    const input = query.trim().toUpperCase();
    if (!input) return;

    const pk = getParentKey(input);
    setParentKey(pk);
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const startTime = Date.now();

      const res = await apiRequest(`/tickets/search/${pk}`);

      // Ensure at least 4 seconds of loading
      const elapsed = Date.now() - startTime;
      const minLoading = 4000;
      if (elapsed < minLoading) {
        await new Promise((r) => setTimeout(r, minLoading - elapsed));
      }

      setLoading(false);

      if (!res || res.type === "error") {
        setError(res?.message || "Not found");
        return;
      }

      setResult({ ...res, input });

      // OPEN TIMELINE AUTOMATICALLY
      setTimelineKey(res.parent?.issue_key || pk);
      setTimelineOpen(true);

      // highlight and redirect logic
      if (res.parent?.issue_key) {
        // Store both the key to highlight and the intent to scroll+highlight
        // Tickets.jsx reads these on mount: scrolls to the card, highlights for 2s, then clears.
        localStorage.setItem("highlight_ticket", res.parent.issue_key);
        localStorage.setItem("highlight_ticket_scroll", "true");
        setRedirecting(true);

        setTimeout(() => {
          window.open("/tickets", "_blank");
          setRedirecting(false);
        }, 2000);
      }
    } catch (err) {
      setLoading(false);
      setError("Server error while searching");
    }
  }

  function handleClear() {
    setQuery("");
    setResult(null);
    setError(null);
    setParentKey("");
    setTimelineOpen(false);
    setTimelineKey("");
  }

  const matchedChild = result
    ? result.children?.find(
      (c) =>
        (c.child_key || "").trim().toUpperCase() === result.input ||
        (c.issue_key || "").trim().toUpperCase() === result.input
    )
    : null;

  const hasResult = !loading && result;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#080c16",
        position: "relative",
        overflowX: "hidden",
      }}
    >
      {/* Ambient background glows */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          zIndex: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "-10%",
            left: "15%",
            width: "600px",
            height: "600px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(99,102,241,0.07) 0%, transparent 70%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-10%",
            right: "10%",
            width: "500px",
            height: "500px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(37,99,235,0.06) 0%, transparent 70%)",
          }}
        />
        {/* Subtle grid */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@400;600;700;800&display=swap');

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%,100% { opacity: 0.5; }
          50%      { opacity: 1; }
        }
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes blink {
          0%,100% { opacity: 1; }
          50%      { opacity: 0; }
        }
        .search-input::placeholder { color: #3d4f6e; }
        .search-input:focus { outline: none; }
        .timeline-panel { animation: fadeUp 0.35s ease both; }
        .results-panel  { animation: fadeUp 0.35s ease 0.08s both; }
        .card-animate   { animation: slideUp 0.3s ease both; }
      `}</style>

      <div style={{ position: "relative", zIndex: 1 }}>
        {/* ── TOP SEARCH HEADER ── */}
        <div
          style={{
            maxWidth: hasResult ? "none" : "680px",
            margin: "0 auto",
            padding: hasResult ? "28px 28px 0" : "80px 24px 0",
            transition: "all 0.4s ease",
          }}
        >
          {/* Brand header — only shown before results */}
          {!hasResult && (
            <div
              style={{
                textAlign: "center",
                marginBottom: "36px",
                animation: "fadeUp 0.5s ease both",
              }}
            >
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "56px",
                  height: "56px",
                  borderRadius: "16px",
                  background: "linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)",
                  boxShadow: "0 8px 32px rgba(99,102,241,0.35)",
                  marginBottom: "20px",
                }}
              >
                <svg width="26" height="26" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h1
                style={{
                  fontFamily: "'Syne', sans-serif",
                  fontSize: "36px",
                  fontWeight: 800,
                  color: "#f1f5f9",
                  margin: "0 0 8px",
                  letterSpacing: "-0.02em",
                }}
              >
                Ticket Search
              </h1>
              <p
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "12px",
                  color: "#475569",
                  letterSpacing: "0.06em",
                }}
              >
                Search and track your tickets instantly
              </p>
            </div>
          )}

          {/* Compact header when results are showing */}
          {hasResult && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginBottom: "20px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)",
                  flexShrink: 0,
                }}
              >
                <svg width="18" height="18" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <span
                style={{
                  fontFamily: "'Syne', sans-serif",
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "#e2e8f0",
                }}
              >
                Ticket Search
              </span>
            </div>
          )}

          {/* ── SEARCH BAR ── */}
          <div
            style={{
              background: "rgba(15,20,35,0.8)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(99,102,241,0.2)",
              borderRadius: "16px",
              padding: "6px",
              boxShadow: "0 4px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
              marginBottom: hasResult ? "0" : "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "44px",
                  height: "44px",
                  borderRadius: "12px",
                  background: "rgba(99,102,241,0.1)",
                  flexShrink: 0,
                }}
              >
                <svg width="20" height="20" fill="none" stroke="#818cf8" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>

              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Enter Jira ID (e.g., IMM-101, PROJ-456)"
                className="search-input"
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  color: "#e2e8f0",
                  fontSize: "14px",
                  fontFamily: "'JetBrains Mono', monospace",
                  padding: "8px 0",
                  letterSpacing: "0.03em",
                }}
              />

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {(result || error) && (
                  <button
                    onClick={handleClear}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "10px",
                      background: "rgba(248,113,113,0.08)",
                      border: "1px solid rgba(248,113,113,0.2)",
                      color: "#f87171",
                      fontSize: "12px",
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 600,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      letterSpacing: "0.04em",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "rgba(248,113,113,0.16)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(248,113,113,0.08)";
                    }}
                  >
                    Clear
                  </button>
                )}
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  style={{
                    padding: "8px 22px",
                    borderRadius: "10px",
                    background: loading
                      ? "rgba(99,102,241,0.3)"
                      : "linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)",
                    border: "none",
                    color: "#fff",
                    fontSize: "12px",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontWeight: 700,
                    cursor: loading ? "not-allowed" : "pointer",
                    boxShadow: loading ? "none" : "0 4px 20px rgba(99,102,241,0.4)",
                    transition: "all 0.15s ease",
                    letterSpacing: "0.06em",
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
            </div>
          </div>

          {/* Search tips — only before results */}
          {!hasResult && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "24px",
                marginTop: "12px",
              }}
            >
              {[
                { dot: "#6366f1", label: "Press Enter to search" },
                { dot: "#3b82f6", label: "Format: PROJECT-123" },
              ].map((tip) => (
                <div
                  key={tip.label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "10px",
                    color: "#475569",
                    letterSpacing: "0.04em",
                  }}
                >
                  <div
                    style={{
                      width: "5px",
                      height: "5px",
                      borderRadius: "50%",
                      background: tip.dot,
                    }}
                  />
                  {tip.label}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── RESULTS AREA ── */}
        <div style={{ padding: hasResult ? "16px 28px 40px" : "24px" }}>
          {/* Loading state */}
          {loading && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                paddingTop: "60px",
                gap: "16px",
              }}
            >
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  border: "2px solid rgba(99,102,241,0.15)",
                  borderTop: "2px solid #6366f1",
                  animation: "spin 0.9s linear infinite",
                }}
              />
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "11px",
                  color: "#475569",
                  letterSpacing: "0.08em",
                  animation: "pulse 1.5s ease-in-out infinite",
                }}
              >
                🔄 Searching ticket {parentKey}...
              </div>
            </div>
          )}

          {/* Error state */}
          {!loading && error && (
            <div
              style={{
                maxWidth: "480px",
                margin: "40px auto",
                padding: "16px 20px",
                background: "rgba(248,113,113,0.06)",
                border: "1px solid rgba(248,113,113,0.18)",
                borderRadius: "12px",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "12px",
                color: "#f87171",
                textAlign: "center",
                letterSpacing: "0.04em",
              }}
            >
              ❌ {error}
            </div>
          )}

          {/* ── TWO-COLUMN LAYOUT ── */}
          {hasResult && (
            <div
              style={{
                display: "flex",
                gap: "20px",
                alignItems: "flex-start",
                minHeight: "calc(100vh - 180px)",
              }}
            >
              {/* LEFT — Timeline panel */}
              <div
                className="timeline-panel"
                style={{
                  width: "480px",
                  flexShrink: 0,
                  height: "calc(100vh - 180px)",
                  position: "sticky",
                  top: "20px",
                  borderRadius: "16px",
                  overflow: "hidden",
                  border: "1px solid rgba(99,102,241,0.15)",
                  boxShadow: "0 4px 40px rgba(0,0,0,0.3)",
                }}
              >
                <TicketTimelineModal
                  issueKey={timelineKey || result.parent?.issue_key}
                  open={true}
                  onClose={() => setTimelineOpen(false)}
                />
              </div>

              {/* RIGHT — Cards panel */}
              <div
                className="results-panel"
                style={{
                  flex: 1,
                  minWidth: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                }}
              >
                {/* Matched child ticket */}
                {matchedChild && (
                  <div
                    className="card-animate bg-yellow/5 border border-yellow/20 rounded-xl p-4 animate-slideUp"
                    style={{ animationDelay: "0.05s" }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-yellow text-xs font-bold">
                          {matchedChild.issue_key}
                        </span>

                        {/* ✅ APP + COMPONENT BADGE (same as TicketCard) */}
                        <span
                          className="text-[0.6rem] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 font-mono"
                          title={`${matchedChild.app_name || "General"} | ${matchedChild.component_name || "General"}`}
                        >
                          {matchedChild.app_name || "General"} | {matchedChild.component_name || "General"}
                        </span>
                      </div>
                      <span className={`font-mono text-xs px-2 py-0.5 rounded border ${matchedChild.status === "Completed" ? "text-green border-green/20 bg-green/5" : "text-yellow border-yellow/20 bg-yellow/5"}`}>
                        {matchedChild.status === "Completed" ? "✔ Completed" : "● Open"}
                      </span>
                    </div>
                    <div className="text-sm space-y-1 text-slate-300">
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Name</span>
                          {matchedChild.name || "-"}
                        </div>
                        <div>
                          <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Email</span>
                          <span className="truncate block">{matchedChild.email || "-"}</span>
                        </div>
                      </div>
                      <div>
                        <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Summary</span>
                        {matchedChild.summary || "-"}
                      </div>
                      <div>
                        <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Description</span>
                        {matchedChild.description || "-"}
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-yellow/10">
                      <button
                        onClick={() => window.open(`${import.meta.env.VITE_JIRA_BASE_URL}/browse/${matchedChild.issue_key}`, "_blank")}
                        className="w-full bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-400 text-[0.65rem] font-bold py-2 px-3 rounded-xl font-mono transition-all"
                      >
                        🔗 Open in Jira
                      </button>
                    </div>
                  </div>
                )}

                {/* Parent ticket */}
                {result.parent && (
                  <div
                    className="border-t border-purple/20 pt-4 card-animate"
                    style={{ animationDelay: "0.1s" }}
                  >
                    <div className="font-mono text-xs text-muted mb-2">🔗 Parent Ticket</div>
                    <div className="bg-surface border border-purple/15 rounded-2xl overflow-hidden animate-slideUp">
                      <div className="flex items-center justify-between px-4 py-3 bg-surface2 border-b border-purple/15">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-yellow text-sm font-bold">
                            {result.parent.issue_key}
                          </span>

                          {/* ✅ APP + COMPONENT BADGE */}
                          <span
                            className="text-[0.6rem] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 font-mono"
                            title={`${result.parent.app_name || "General"} | ${result.parent.component_name || "General"}`}
                          >
                            {result.parent.app_name || "General"} | {result.parent.component_name || "General"}
                          </span>
                        </div>
                        <span className={`font-mono text-xs px-2.5 py-0.5 rounded-full border ${result.parent.status === "Completed" ? "text-green border-green/20 bg-green/5" : "text-yellow border-yellow/20 bg-yellow/5"}`}>
                          {result.parent.status === "Completed" ? "✔ Completed" : "● Open"}
                        </span>
                      </div>
                      <div className="px-4 py-3 space-y-2 text-sm">
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                          <div>
                            <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Name</span>
                            <span className="text-slate-200">{result.parent.name || "-"}</span>
                          </div>
                          <div>
                            <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Email</span>
                            <span className="text-slate-200 truncate block">{result.parent.email || "-"}</span>
                          </div>
                        </div>
                        <div>
                          <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Summary</span>
                          <span className="text-slate-200 text-xs">{result.parent.summary || "-"}</span>
                        </div>
                        <div>
                          <span className="font-mono text-[0.6rem] text-muted uppercase block mb-0.5">Description</span>
                          <span className="text-slate-300 text-xs line-clamp-2">{result.parent.description || "-"}</span>
                        </div>
                      </div>
                      <div className="px-4 py-3 border-t border-purple/10 flex gap-2">
                        <button
                          onClick={() => window.open(`${import.meta.env.VITE_JIRA_BASE_URL}/browse/${result.parent.issue_key}`, "_blank")}
                          className="flex-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[0.65rem] font-bold py-2 px-3 rounded-xl font-mono transition-all hover:bg-blue-500/20"
                        >
                          🔗 Open in Jira
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Redirecting notice */}
                {redirecting && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "10px",
                      padding: "14px 20px",
                      background: "rgba(234,179,8,0.06)",
                      border: "1px solid rgba(234,179,8,0.18)",
                      borderRadius: "12px",
                    }}
                  >
                    <div
                      style={{
                        width: "6px",
                        height: "6px",
                        borderRadius: "50%",
                        background: "#eab308",
                        animation: "blink 0.8s ease-in-out infinite",
                      }}
                    />
                    <span
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: "11px",
                        color: "#eab308",
                        letterSpacing: "0.06em",
                        animation: "pulse 1.2s ease-in-out infinite",
                      }}
                    >
                      Redirecting to dashboard...
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}