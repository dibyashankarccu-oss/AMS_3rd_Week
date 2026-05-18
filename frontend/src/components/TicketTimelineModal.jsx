import { useEffect, useState } from "react";
import { apiRequest } from "../api/apiClient";

function toIST(utcDateStr) {
  if (!utcDateStr) return "-";
  const date = new Date(utcDateStr);
  const istOffset = 5.5 * 60 * 60 * 1000;
  const istTime = new Date(date.getTime() + istOffset);
  return istTime.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

const EVENT_ICONS = {
  created:   "▶",
  updated:   "◈",
  assigned:  "⊕",
  commented: "◎",
  resolved:  "✔",
  closed:    "⊗",
  reopened:  "↺",
  default:   "◆",
};

function getEventIcon(eventType = "") {
  const lower = eventType.toLowerCase();
  for (const key of Object.keys(EVENT_ICONS)) {
    if (lower.includes(key)) return EVENT_ICONS[key];
  }
  return EVENT_ICONS.default;
}

// All colours stay within the product's blue/indigo/violet palette
// for visual consistency + readability on dark navy backgrounds
function getEventColor(eventType = "") {
  const lower = eventType.toLowerCase();
  if (lower.includes("creat"))
    return { dot: "#818cf8", text: "#a5b4fc", dim: "rgba(99,102,241,0.1)", label: "#6366f1" };
  if (lower.includes("resolv") || lower.includes("clos") || lower.includes("complet"))
    return { dot: "#34d399", text: "#6ee7b7", dim: "rgba(52,211,153,0.08)", label: "#10b981" };
  if (lower.includes("assign"))
    return { dot: "#60a5fa", text: "#93c5fd", dim: "rgba(96,165,250,0.08)", label: "#3b82f6" };
  if (lower.includes("comment"))
    return { dot: "#c084fc", text: "#d8b4fe", dim: "rgba(192,132,252,0.08)", label: "#a855f7" };
  if (lower.includes("reopen"))
    return { dot: "#fb923c", text: "#fdba74", dim: "rgba(251,146,60,0.08)", label: "#f97316" };
  if (lower.includes("updat"))
    return { dot: "#38bdf8", text: "#7dd3fc", dim: "rgba(56,189,248,0.08)", label: "#0ea5e9" };
  return { dot: "#a78bfa", text: "#c4b5fd", dim: "rgba(167,139,250,0.08)", label: "#8b5cf6" };
}

function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `${r},${g},${b}`;
}

function useCounter(active) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!active) { setCount(0); return; }
    const id = setInterval(() => setCount((c) => c + Math.floor(Math.random() * 14 + 2)), 90);
    return () => clearInterval(id);
  }, [active]);
  return count;
}

export default function TicketTimelineModal({ issueKey, open, onClose }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const scanCount = useCounter(loading);

  useEffect(() => {
    if (!open || !issueKey) return;
    async function fetchTimeline() {
      setLoading(true);
      try {
        const res = await apiRequest(`/tickets/${issueKey}/timeline`);
        setEvents(res?.events || []);
      } catch (e) {
        setEvents([]);
      }
      setLoading(false);
    }
    fetchTimeline();
  }, [issueKey, open]);

  if (!open) return null;

  const now = new Date().toISOString().replace("T", " ").slice(0, 19);

  return (
    <div
      className="w-full h-full flex flex-col"
      style={{
        background: "linear-gradient(180deg, #0d1220 0%, #0b0f1a 100%)",
        borderRight: "1px solid rgba(99,102,241,0.15)",
        fontFamily: "'JetBrains Mono', 'Courier New', monospace",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        @keyframes termSlide  { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        @keyframes termBlink  { 0%,49%{opacity:1} 50%,100%{opacity:0} }
        @keyframes barMove    { 0%{transform:translateX(-100%)} 100%{transform:translateX(400%)} }
        @keyframes termPulse  { 0%,100%{opacity:0.35} 50%{opacity:1} }
        @keyframes scanSwipe  { 0%{top:-8%} 100%{top:108%} }
        @keyframes bootIn     { from{opacity:0} to{opacity:1} }

        .tl-body::-webkit-scrollbar       { width: 3px; }
        .tl-body::-webkit-scrollbar-track { background: transparent; }
        .tl-body::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.25); border-radius: 2px; }

        .tl-card-row:hover .tl-card {
          border-color: rgba(99,102,241,0.3) !important;
          background: rgba(99,102,241,0.05) !important;
        }
        .tl-card-row:hover .tl-dot {
          box-shadow: 0 0 12px 2px rgba(99,102,241,0.35) !important;
        }
      `}</style>

      {/* Subtle CRT scanline sweep — very faint to keep readability */}
      <div style={{ position:"absolute", inset:0, pointerEvents:"none", zIndex:20, overflow:"hidden" }}>
        <div style={{
          position:"absolute", left:0, right:0, height:"5%",
          background:"linear-gradient(180deg,transparent,rgba(99,102,241,0.015),transparent)",
          animation:"scanSwipe 8s linear infinite",
        }}/>
      </div>

      {/* ── HEADER ── */}
      <div style={{
        flexShrink: 0,
        borderBottom: "1px solid rgba(99,102,241,0.13)",
        background: "rgba(10,14,26,0.95)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>

        {/* Window chrome bar */}
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"6px 14px",
          borderBottom:"1px solid rgba(99,102,241,0.08)",
          background:"rgba(7,10,20,0.9)",
        }}>
          {/* Traffic lights + label */}
          <div style={{ display:"flex", gap:"5px", alignItems:"center" }}>
            <div style={{ width:8, height:8, borderRadius:"50%", background:"#ff5f56", opacity:0.85 }}/>
            <div style={{ width:8, height:8, borderRadius:"50%", background:"#ffbd2e", opacity:0.85 }}/>
            <div style={{ width:8, height:8, borderRadius:"50%", background:"#27c93f", opacity:0.85 }}/>
            <span style={{
              marginLeft:10, fontSize:"9px", letterSpacing:"0.14em",
              textTransform:"uppercase", color:"rgba(99,102,241,0.45)",
              fontWeight:600,
            }}>
              terminal — activity log
            </span>
          </div>

          {/* Close */}
          <button
            onClick={onClose}
            style={{
              fontSize:"9px", letterSpacing:"0.08em", fontWeight:600,
              color:"#f87171",
              background:"rgba(248,113,113,0.07)",
              border:"1px solid rgba(248,113,113,0.2)",
              borderRadius:"5px", padding:"3px 11px",
              cursor:"pointer", fontFamily:"inherit", transition:"all 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(248,113,113,0.16)";
              e.currentTarget.style.borderColor = "rgba(248,113,113,0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(248,113,113,0.07)";
              e.currentTarget.style.borderColor = "rgba(248,113,113,0.2)";
            }}
          >
            ✕ close
          </button>
        </div>

        {/* Shell prompt */}
        <div style={{ padding:"10px 14px 9px" }}>
          {/* Command line */}
          <div style={{
            display:"flex", alignItems:"center", gap:"5px",
            marginBottom:"6px", flexWrap:"wrap",
          }}>
            <span style={{ color:"#818cf8", fontSize:"10px", fontWeight:600 }}>user@nexus</span>
            <span style={{ color:"rgba(99,102,241,0.35)", fontSize:"10px" }}>:</span>
            <span style={{ color:"#60a5fa", fontSize:"10px" }}>~/tickets</span>
            <span style={{ color:"rgba(99,102,241,0.4)", fontSize:"10px" }}>$</span>
            <span style={{ color:"#e2e8f0", fontSize:"10px", letterSpacing:"0.03em" }}>
              fetch --timeline
            </span>
            <span style={{
              color:"#a78bfa", fontSize:"10px", fontWeight:700, letterSpacing:"0.05em",
            }}>
              {issueKey}
            </span>
            <span style={{
              display:"inline-block", width:"6px", height:"11px",
              background:"#6366f1",
              animation:"termBlink 1.1s step-end infinite",
              verticalAlign:"middle", marginLeft:"1px", borderRadius:"1px",
            }}/>
          </div>

          {/* Status meta line */}
          <div style={{
            display:"flex", alignItems:"center", gap:"10px", flexWrap:"wrap",
            fontSize:"9px", letterSpacing:"0.08em",
          }}>
            <span style={{ color:"rgba(99,102,241,0.4)" }}>▸</span>
            <span style={{ color:"rgba(148,163,184,0.55)" }}>{now} IST</span>
            <span style={{ color:"rgba(99,102,241,0.2)" }}>│</span>

            {!loading && events.length > 0 && (
              <span style={{ color:"rgba(148,163,184,0.55)" }}>
                records:{" "}
                <span style={{ color:"#a78bfa", fontWeight:600 }}>
                  {events.length}
                </span>
              </span>
            )}

            {loading && (
              <span style={{
                color:"rgba(99,102,241,0.6)",
                animation:"termPulse 1.3s ease-in-out infinite",
              }}>
                scanning… {scanCount.toLocaleString()} bytes
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── BODY ── */}
      <div
        className="tl-body"
        style={{ flex:1, padding:"12px 14px 28px", overflowY:"auto" }}
      >

        {/* ── LOADING STATE ── */}
        {loading && (
          <div style={{ paddingTop:"20px", animation:"bootIn 0.3s ease both" }}>
            {[
              "authenticating session…",
              `resolving key ${issueKey}…`,
              "fetching event stream…",
              "parsing payload…",
            ].map((line, i) => (
              <div key={i} style={{
                display:"flex", alignItems:"center", gap:"7px",
                fontSize:"10px", color:"rgba(148,163,184,0.6)",
                letterSpacing:"0.05em", marginBottom:"8px",
                animationDelay:`${i * 0.1}s`,
              }}>
                <span style={{ color:"#6366f1", flexShrink:0 }}>›</span>
                <span>{line}</span>
                <span style={{ color:"#6366f1", animation:"termBlink 0.7s step-end infinite" }}>_</span>
              </div>
            ))}

            {/* Indigo progress bar */}
            <div style={{
              marginTop:"20px", height:"2px",
              background:"rgba(99,102,241,0.1)", borderRadius:"2px", overflow:"hidden",
            }}>
              <div style={{
                height:"100%", width:"25%",
                background:"linear-gradient(90deg, transparent, #6366f1, #a78bfa, transparent)",
                animation:"barMove 1.4s linear infinite",
              }}/>
            </div>
          </div>
        )}

        {/* ── EMPTY STATE ── */}
        {!loading && events.length === 0 && (
          <div style={{ paddingTop:"36px", animation:"bootIn 0.3s ease both" }}>
            <div style={{
              fontSize:"9px", color:"rgba(99,102,241,0.4)",
              letterSpacing:"0.1em", marginBottom:"8px",
            }}>
              $ query --issue {issueKey} --events all
            </div>
            <div style={{
              fontSize:"10px", color:"#f87171",
              letterSpacing:"0.06em", marginBottom:"6px",
            }}>
              ✕ no records found
            </div>
            <div style={{ display:"flex", alignItems:"center", gap:"4px" }}>
              <span style={{ fontSize:"9px", color:"rgba(99,102,241,0.35)" }}>$</span>
              <span style={{ animation:"termBlink 1s step-end infinite", color:"#6366f1", fontSize:"11px" }}>▋</span>
            </div>
          </div>
        )}

        {/* ── TIMELINE ── */}
        {!loading && events.length > 0 && (
          <div style={{ animation:"bootIn 0.35s ease both" }}>

            {/* Boot line */}
            <div style={{
              display:"flex", alignItems:"center", gap:"7px",
              fontSize:"9px", letterSpacing:"0.08em",
              marginBottom:"16px", color:"rgba(99,102,241,0.5)",
            }}>
              <span style={{
                color:"#34d399", fontWeight:700, letterSpacing:"0.1em",
              }}>[ OK ]</span>
              <span>stream ready —</span>
              <span style={{ color:"#a78bfa", fontWeight:600 }}>
                {events.length} event{events.length !== 1 ? "s" : ""}
              </span>
              <span style={{ color:"rgba(99,102,241,0.25)" }}>↓</span>
            </div>

            <div style={{ position:"relative" }}>
              {/* Vertical timeline rail */}
              <div style={{
                position:"absolute",
                left:"10px", top:"6px", bottom:"6px",
                width:"1px",
                background:"linear-gradient(180deg, rgba(99,102,241,0.4) 0%, rgba(99,102,241,0.04) 100%)",
              }}/>

              <div style={{ display:"flex", flexDirection:"column", gap:"9px" }}>
                {events.map((ev, idx) => {
                  const color = getEventColor(ev.event);
                  const icon  = getEventIcon(ev.event);
                  const rgb   = hexToRgb(color.dot);

                  return (
                    <div
                      key={idx}
                      className="tl-card-row"
                      style={{
                        display:"flex", gap:"10px", alignItems:"flex-start",
                        animation:"termSlide 0.3s ease both",
                        animationDelay:`${idx * 0.04}s`,
                        position:"relative", zIndex:1,
                      }}
                    >
                      {/* Timeline dot */}
                      <div
                        className="tl-dot"
                        style={{
                          width:"21px", height:"21px", borderRadius:"50%",
                          background: color.dim,
                          border:`1.5px solid ${color.dot}`,
                          display:"flex", alignItems:"center", justifyContent:"center",
                          flexShrink:0, fontSize:"9px", color:color.dot,
                          boxShadow:`0 0 8px rgba(${rgb},0.25)`,
                          transition:"box-shadow 0.2s",
                        }}
                      >
                        {icon}
                      </div>

                      {/* Event card */}
                      <div
                        className="tl-card"
                        style={{
                          flex:1,
                          background:"rgba(15,20,35,0.65)",
                          border:"1px solid rgba(99,102,241,0.1)",
                          borderRadius:"8px",
                          padding:"9px 12px",
                          backdropFilter:"blur(6px)",
                          transition:"border-color 0.2s, background 0.2s",
                        }}
                      >
                        {/* Top row: index + event type pill + timestamp */}
                        <div style={{
                          display:"flex", alignItems:"center",
                          justifyContent:"space-between",
                          gap:"8px", flexWrap:"wrap",
                          marginBottom:"6px",
                        }}>
                          {/* Left: index label + event pill */}
                          <div style={{ display:"flex", alignItems:"center", gap:"6px" }}>
                            <span style={{
                              fontSize:"8px",
                              color:"rgba(99,102,241,0.35)",
                              letterSpacing:"0.1em",
                              fontWeight:500,
                            }}>
                              #{String(idx + 1).padStart(2, "0")}
                            </span>

                            <span style={{
                              fontSize:"9px", fontWeight:700,
                              color:color.text,
                              background:color.dim,
                              border:`1px solid rgba(${rgb},0.28)`,
                              borderRadius:"4px",
                              padding:"2px 8px",
                              letterSpacing:"0.1em",
                              textTransform:"uppercase",
                            }}>
                              {ev.event}
                            </span>
                          </div>

                          {/* Right: timestamp */}
                          <span style={{
                            fontSize:"8px",
                            color:"#cbd5e1",
                            letterSpacing:"0.05em",
                            whiteSpace:"nowrap",
                          }}>
                            {new Date(ev.created_at_ist).toLocaleString("en-IN")}
                          </span>
                        </div>

                        {/* Thin accent divider */}
                        <div style={{
                          height:"1px", marginBottom:"7px",
                          background:`linear-gradient(90deg, rgba(${rgb},0.22) 0%, transparent 70%)`,
                        }}/>

                        {/* Details text — most important: readable */}
                        {ev.details && (
                          <div style={{
                            fontSize:"12px",
                            color:"#cbd5e1",
                            lineHeight:"1.6",
                            letterSpacing:"0.01em",
                          }}>
                            <span style={{
                              color:"rgba(99,102,241,0.5)",
                              marginRight:"6px",
                              fontSize:"9px",
                            }}>›</span>
                            {ev.details}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* EOF marker */}
              <div style={{
                marginTop:"16px", paddingLeft:"32px",
                display:"flex", alignItems:"center", gap:"6px",
                fontSize:"9px", color:"rgba(99,102,241,0.22)",
                letterSpacing:"0.1em",
              }}>
                <span>— end of log —</span>
                <span style={{ animation:"termBlink 1.1s step-end infinite", color:"#6366f1" }}>▋</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}