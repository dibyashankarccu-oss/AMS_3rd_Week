import { useEffect, useState } from "react";

export default function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/logs");
      const data = await res.json();
      setLogs(data.logs || []);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, []);

  // =========================
  // SEVERITY COLOR ENGINE
  // =========================
  const getSeverityStyle = (log) => {
    if (log.severity === "critical")
      return "text-red-400 border-red-500/40 bg-red-500/5";
    if (log.severity === "warning")
      return "text-amber-400 border-amber-500/40 bg-amber-500/5";
    if (log.severity === "slow")
      return "text-orange-400 border-orange-500/40 bg-orange-500/5";
    return "text-emerald-400 border-emerald-600/40 bg-emerald-500/5";
  };

  const getSeverityDot = (log) => {
    if (log.severity === "critical") return "bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.8)]";
    if (log.severity === "warning") return "bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]";
    if (log.severity === "slow") return "bg-orange-400 shadow-[0_0_6px_rgba(251,146,60,0.8)]";
    return "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]";
  };

  const getStatusStyle = (log) => {
    if (log.status_code >= 500) return "text-red-400 bg-red-500/10 border border-red-500/20";
    if (log.status_code >= 400) return "text-amber-400 bg-amber-500/10 border border-amber-500/20";
    return "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20";
  };

  const getMethodStyle = (method) => {
    if (method === "GET") return "text-sky-300 bg-sky-500/10 border border-sky-500/20";
    if (method === "POST") return "text-violet-300 bg-violet-500/10 border border-violet-500/20";
    if (method === "PUT") return "text-amber-300 bg-amber-500/10 border border-amber-500/20";
    if (method === "DELETE") return "text-red-300 bg-red-500/10 border border-red-500/20";
    if (method === "PATCH") return "text-teal-300 bg-teal-500/10 border border-teal-500/20";
    return "text-slate-300 bg-slate-500/10 border border-slate-500/20";
  };

  const totalCritical = logs.filter(l => l.severity === "critical").length;
  const totalWarning = logs.filter(l => l.severity === "warning").length;

  return (
    <div
      className="min-h-screen text-slate-200 p-6 md:p-8"
      style={{
        background: "linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a0f1e 100%)",
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');

        .grid-bg {
          background-image:
            linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
          background-size: 40px 40px;
        }
        .scan-line {
          position: relative;
          overflow: hidden;
        }
        .scan-line::after {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 2px;
          background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
          animation: scan 3s linear infinite;
          pointer-events: none;
          z-index: 10;
        }
        @keyframes scan {
          0% { top: 0%; opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        .pulse-dot {
          animation: pulse-glow 2s ease-in-out infinite;
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }
        .row-hover:hover {
          background: rgba(99,102,241,0.04);
        }
        .badge {
          display: inline-flex;
          align-items: center;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        ::-webkit-scrollbar { height: 4px; width: 4px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #1e2a3a; border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: #2d3f54; }
      `}</style>

      <div className="grid-bg fixed inset-0 pointer-events-none" />

      <div className="relative z-10 max-w-[1600px] mx-auto">

        {/* ── HEADER ── */}
        <div className="mb-8 flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-2 h-2 rounded-full bg-indigo-400 pulse-dot shadow-[0_0_8px_rgba(129,140,248,0.9)]" />
              <span className="text-indigo-400 text-[10px] tracking-[0.25em] uppercase font-medium">Live Stream</span>
            </div>
            <h1
              className="text-2xl md:text-3xl font-bold tracking-tight text-white"
              style={{ fontFamily: "'Syne', sans-serif", letterSpacing: "-0.01em" }}
            >
              AMS Observability Console
            </h1>
            <p className="text-slate-500 text-xs mt-1 tracking-wide">
              Realtime backend telemetry stream
            </p>
          </div>

          {/* Live badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
            <span className="text-emerald-400 text-[10px] font-semibold tracking-[0.15em] uppercase">Polling</span>
          </div>
        </div>

        {/* ── STAT CARDS ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            { label: "Total Events", value: logs.length, colorRgb: "99,102,241", textRgb: "199,210,254", icon: "◈" },
            {
              label: "Last Event",
              value: logs[0]?.timestamp ? new Date(logs[0].timestamp).toLocaleTimeString() : "--",
              colorRgb: "14,165,233",
              textRgb: "186,230,253",
              icon: "◷",
            },
            { label: "Critical", value: totalCritical, colorRgb: "239,68,68", textRgb: "254,202,202", icon: "⚑" },
            { label: "Warnings", value: totalWarning, colorRgb: "245,158,11", textRgb: "254,243,199", icon: "⚠" },
          ].map(({ label, value, colorRgb, textRgb, icon }) => (
            <div
              key={label}
              className="rounded-xl border p-4 backdrop-blur-sm"
              style={{
                background: `rgba(${colorRgb},0.04)`,
                borderColor: `rgba(${colorRgb},0.15)`,
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-[10px] uppercase tracking-widest">{label}</span>
                <span className="text-lg" style={{ color: `rgba(${colorRgb},0.7)` }}>{icon}</span>
              </div>
              <div className="text-xl font-bold tabular-nums" style={{ color: `rgba(${textRgb},1)` }}>
                {value}
              </div>
            </div>
          ))}
        </div>

        {/* ── LOADING ── */}
        {loading && (
          <div className="flex items-center gap-3 mb-4 text-indigo-400 text-xs tracking-widest">
            <div className="w-3 h-3 border border-indigo-400 border-t-transparent rounded-full animate-spin" />
            INITIALIZING LOG STREAM...
          </div>
        )}

        {/* ── TABLE ── */}
        <div
          className="scan-line rounded-xl border border-slate-800/80 overflow-hidden"
          style={{ background: "rgba(13,17,23,0.9)", backdropFilter: "blur(12px)" }}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left" style={{ fontSize: "11px" }}>

              {/* HEAD */}
              <thead>
                <tr
                  className="border-b border-slate-800"
                  style={{ background: "rgba(15,20,30,0.95)" }}
                >
                  {["Time", "Trace ID", "Method", "Endpoint", "Status", "Code", "Latency", "Severity", "Service", "IP"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-[10px] tracking-[0.15em] uppercase font-semibold text-slate-500 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>

              {/* BODY */}
              <tbody className="divide-y divide-slate-800/50">
                {logs.map((log, i) => (
                  <tr key={i} className="row-hover transition-colors duration-150">

                    {/* TIME */}
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap tabular-nums">
                      {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "--"}
                    </td>

                    {/* TRACE */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-cyan-400/80 font-medium tracking-wider">
                        {log.request_id?.slice(0, 8) || "--"}
                      </span>
                    </td>

                    {/* METHOD */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`badge ${getMethodStyle(log.method)}`}>
                        {log.method || "--"}
                      </span>
                    </td>

                    {/* ENDPOINT */}
                    <td className="px-4 py-3 text-slate-200 max-w-[220px] truncate">
                      {log.endpoint || log.path || "--"}
                    </td>

                    {/* STATUS */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`badge ${getStatusStyle(log)}`}>
                        {log.status || "ok"}
                      </span>
                    </td>

                    {/* CODE */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`font-bold tabular-nums ${
                          log.status_code >= 500 ? "text-red-400"
                          : log.status_code >= 400 ? "text-amber-400"
                          : "text-slate-300"
                        }`}
                      >
                        {log.status_code || "--"}
                      </span>
                    </td>

                    {/* LATENCY */}
                    <td className="px-4 py-3 whitespace-nowrap tabular-nums">
                      <span
                        className={`font-medium ${
                          log.latency_ms > 2000 ? "text-red-400"
                          : log.latency_ms > 1000 ? "text-amber-400"
                          : "text-violet-300"
                        }`}
                      >
                        {log.latency_ms || "--"}
                        <span className="text-slate-600 font-normal ml-0.5">ms</span>
                      </span>
                    </td>

                    {/* SEVERITY */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${getSeverityDot(log)}`} />
                        <span className={`badge border ${getSeverityStyle(log)}`}>
                          {log.severity || "info"}
                        </span>
                      </div>
                    </td>

                    {/* SERVICE */}
                    <td className="px-4 py-3 whitespace-nowrap text-slate-400">
                      {log.service_group || "backend"}
                    </td>

                    {/* IP */}
                    <td className="px-4 py-3 whitespace-nowrap text-slate-600 tabular-nums">
                      {log.client_ip || "--"}
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* TABLE FOOTER */}
          {!loading && logs.length > 0 && (
            <div
              className="px-4 py-2.5 border-t border-slate-800/60 flex items-center justify-between"
              style={{ background: "rgba(10,14,26,0.8)" }}
            >
              <span className="text-[10px] text-slate-600 tracking-widest uppercase">
                Showing {logs.length} events
              </span>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-emerald-500 pulse-dot" />
                <span className="text-[10px] text-slate-600 tracking-widest uppercase">Live</span>
              </div>
            </div>
          )}
        </div>

        {/* ── EMPTY STATE ── */}
        {!loading && logs.length === 0 && (
          <div className="mt-10 flex flex-col items-center justify-center gap-3 text-center py-16 rounded-xl border border-red-500/10"
            style={{ background: "rgba(239,68,68,0.03)" }}
          >
            <div className="text-4xl text-red-500/30">⊘</div>
            <p className="text-red-400 text-sm font-semibold tracking-widest uppercase">No Telemetry Data Found</p>
            <p className="text-slate-600 text-xs">The log stream returned no events. Check your backend connection.</p>
          </div>
        )}

        {/* ── FOOTER ── */}
        <div className="mt-6 flex items-center justify-between text-[10px] text-slate-700 tracking-wider">
          <span>AMS OBSERVABILITY · v1.0</span>
        </div>
      </div>
    </div>
  );
}