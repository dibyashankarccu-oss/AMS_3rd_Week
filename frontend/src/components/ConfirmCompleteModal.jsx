import { useEffect } from "react";

export default function ConfirmCompleteModal({
  open,
  issueKey,
  openChildren = [],
  onCancel,
  onConfirm,
}) {
  if (!open) return null;

  // close on ESC
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onCancel();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      
      {/* MODAL BOX */}
      <div className="w-[420px] bg-surface border border-purple/20 rounded-2xl shadow-2xl overflow-hidden animate-slideUp">

        {/* HEADER */}
        <div className="px-4 py-3 border-b border-purple/15 bg-surface2">
          <h2 className="text-sm font-bold text-purple font-mono">
            ⚠ Confirm Completion
          </h2>
          <p className="text-[0.65rem] text-slate-400 font-mono mt-1">
            Ticket: {issueKey}
          </p>
        </div>

        {/* BODY */}
        <div className="px-4 py-3 space-y-3">
          <p className="text-xs text-slate-300">
            Some child tickets are still <b>open</b>.  
            Completing this parent will mark all child tickets as <b>Completed</b>.
          </p>

          {/* CHILD LIST */}
          <div className="bg-surface2 border border-purple/10 rounded-lg p-2 max-h-32 overflow-y-auto">
            {openChildren.length > 0 ? (
              openChildren.map((child) => (
                <div
                  key={child}
                  className="text-[0.65rem] text-yellow font-mono py-1 border-b border-purple/10 last:border-none"
                >
                  🔹 {child}
                </div>
              ))
            ) : (
              <p className="text-[0.65rem] text-slate-400">
                No open children
              </p>
            )}
          </div>

          <p className="text-[0.65rem] text-red-400 font-mono">
            ⚠ This action cannot be undone
          </p>
        </div>

        {/* FOOTER */}
        <div className="flex items-center gap-2 px-4 py-3 border-t border-purple/15 bg-surface2">
          
          <button
            onClick={onCancel}
            className="flex-1 bg-surface hover:bg-white/5 border border-purple/20 text-slate-300 text-xs font-mono py-2 rounded-lg transition"
          >
            Cancel
          </button>

          <button
            onClick={onConfirm}
            className="flex-1 bg-red-500/20 hover:bg-red-500/30 border border-red-400/30 text-red-300 text-xs font-mono py-2 rounded-lg transition"
          >
            Confirm Complete
          </button>

        </div>
      </div>
    </div>
  );
}