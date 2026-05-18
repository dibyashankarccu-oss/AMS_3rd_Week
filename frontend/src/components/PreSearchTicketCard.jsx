import { useState } from "react";

export default function PreSearchTicketCard({
  ticket,
  onClose,
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">

      {/* Modal */}
      <div className="w-full max-w-3xl bg-[#151b2b]/95 border border-purple-500/20 rounded-3xl overflow-hidden shadow-2xl shadow-purple-900/30 animate-slideUp">

        {/* Header */}
        <div className="px-6 py-5 border-b border-purple-500/15 bg-gradient-to-r from-purple-500/10 to-blue-500/10">

          <div className="flex items-start justify-between">

            <div>

              {ticket ? (
                <>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-yellow text-lg font-bold">
                      {ticket.issue_key}
                    </span>

                    <span className="px-2 py-1 rounded-full text-[10px] border border-green/20 bg-green/10 text-green">
                      ✔ Historical Match
                    </span>

                    {ticket.llm_score && (
                      <span className="px-2 py-1 rounded-full text-[10px] border border-purple-500/20 bg-purple-500/10 text-purple-300">
                        Match {ticket.llm_score}%
                      </span>
                    )}
                  </div>

                  <div className="mt-2 text-sm text-slate-400">
                    Similar resolved incident found
                  </div>
                </>
              ) : (
                <div className="text-white text-lg font-semibold">
                  No similar ticket found
                </div>
              )}

            </div>

            <button
              onClick={onClose}
              className="w-9 h-9 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 hover:bg-red-500/20 transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">

          {/* NO TICKET STATE */}
          {!ticket && (
            <div className="text-center py-10">
              <div className="text-5xl mb-3">🔍</div>
              <div className="text-slate-300 text-lg">
                No similar completed tickets found
              </div>
            </div>
          )}

          {/* TICKET FOUND STATE */}
          {ticket && (
            <>
              {/* User Info */}
              <div className="grid grid-cols-2 gap-4">

                <div className="bg-surface2 rounded-2xl p-4 border border-purple/10">
                  <div className="font-mono text-[10px] uppercase text-muted mb-2">
                    Name
                  </div>
                  <div className="text-slate-200">
                    {ticket.name || "-"}
                  </div>
                </div>

                <div className="bg-surface2 rounded-2xl p-4 border border-purple/10">
                  <div className="font-mono text-[10px] uppercase text-muted mb-2">
                    Email
                  </div>
                  <div className="text-slate-200 break-all">
                    {ticket.email || "-"}
                  </div>
                </div>

              </div>

              {/* Summary */}
              <div className="bg-surface2 rounded-2xl p-4 border border-purple/10">
                <div className="font-mono text-[10px] uppercase text-muted mb-2">
                  Summary
                </div>
                <div className="text-slate-200">
                  {ticket.summary}
                </div>
              </div>

              {/* Description */}
              <div className="bg-surface2 rounded-2xl p-4 border border-purple/10">
                <div className="font-mono text-[10px] uppercase text-muted mb-2">
                  Description
                </div>

                <div className="text-slate-300 text-sm">
                  {expanded
                    ? ticket.description
                    : ticket.description?.slice(0, 180)
                  }

                  {(ticket.description?.length || 0) > 180 && (
                    <button
                      onClick={() => setExpanded(!expanded)}
                      className="ml-2 text-blue-400 hover:text-blue-300 text-xs"
                    >
                      {expanded ? "Show less" : "Show more"}
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-purple/10 flex gap-3">

          {ticket && (
            <>
              <button
                onClick={() =>
                  window.open(
                    `${import.meta.env.VITE_JIRA_BASE_URL}/browse/${ticket.issue_key}`,
                    "_blank"
                  )
                }
                className="flex-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 py-3 rounded-xl font-mono text-sm hover:bg-blue-500/20 transition"
              >
                🔗 Open in Jira
              </button>

              <button
                onClick={() => {
                  localStorage.setItem("highlight_ticket", ticket.issue_key);
                  window.open("/tickets", "_blank");
                }}
                className="flex-1 bg-purple-500/10 border border-purple-500/20 text-purple-300 py-3 rounded-xl font-mono text-sm hover:bg-purple-500/20 transition"
              >
                📊 Open in Dashboard
              </button>
            </>
          )}

        </div>

      </div>
    </div>
  );
}