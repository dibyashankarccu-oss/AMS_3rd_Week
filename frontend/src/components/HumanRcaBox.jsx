import { useState } from "react";

/**
 * Shown inside RcaModal when confidence === "LOW".
 * Props:
 *   issueKey    – ticket identifier (for display only; submit is handled by parent)
 *   aiAffected  – AI-guessed affected component to pre-fill the field
 *   onSubmit    – async (rootCause, affected) => void   (throws on error)
 */
export default function HumanRcaBox({ issueKey, aiAffected = "", onSubmit }) {
    const [rootCause, setRootCause] = useState("");
    const [affected, setAffected] = useState(aiAffected);
    const [saving, setSaving] = useState(false);
    const [err, setErr] = useState(null);

async function handleSubmit() {
    const trimmed = rootCause.trim();
    if (!trimmed) {
        setErr("Root cause cannot be empty.");
        return;
    }

    setSaving(true);
    setErr(null);

    try {
        await onSubmit(trimmed, affected.trim());
    } catch (e) {
        setErr(e.message || "Save failed");
    } finally {
        setSaving(false);
    }
}
    return (
        <div className="animate-slideUp bg-surface2 border border-yellow/30 rounded-xl p-5 space-y-4">

            {/* ── Header ── */}
            <div className="flex items-start gap-3">
                <span className="text-yellow text-lg flex-shrink-0 mt-0.5">⚠️</span>
                <div>
                    <p className="text-sm font-bold text-yellow leading-tight">Human Review Required</p>
                    <p className="font-mono text-[0.65rem] text-muted mt-1 leading-relaxed">
                        AI confidence is LOW. Please write the confirmed root cause below — it will be
                        stored for future incident matching.
                    </p>
                </div>
            </div>

            {/* ── Root Cause ── */}
            <div className="space-y-1.5">
                <label className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block">
                    Root Cause <span className="text-red normal-case">*</span>
                </label>
                <textarea
                    rows={4}
                    value={rootCause}
                    onChange={e => setRootCause(e.target.value)}
                    placeholder="Describe the confirmed root cause in technical detail…"
                    className="w-full bg-bg border border-yellow/20 focus:border-yellow/50 text-slate-200 rounded-lg px-3 py-2.5 font-mono text-xs leading-relaxed resize-y outline-none transition-colors placeholder:text-muted"
                />
            </div>

            {/* ── Affected Component ── */}
            <div className="space-y-1.5">
                <label className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block">
                    Affected Component <span className="text-muted normal-case">(optional)</span>
                </label>
                <input
                    type="text"
                    value={affected}
                    onChange={e => setAffected(e.target.value)}
                    placeholder="e.g. PostgreSQL connection pool, Auth service…"
                    className="w-full bg-bg border border-yellow/20 focus:border-yellow/50 text-slate-200 rounded-lg px-3 py-2 font-mono text-xs outline-none transition-colors placeholder:text-muted"
                />
            </div>

            {/* ── Error ── */}
            {err && (
                <p className="font-mono text-xs text-red">{err}</p>
            )}

            {/* ── Submit ── */}
            <button
                onClick={handleSubmit}
                disabled={saving}
                className="bg-yellow/10 hover:bg-yellow/20 disabled:opacity-50 disabled:cursor-not-allowed border border-yellow/35 text-yellow text-xs font-bold font-mono py-2 px-5 rounded-xl transition-all duration-200 hover:scale-[1.02]"
            >
                {saving ? "Saving…" : "✍️ Submit Human RCA"}
            </button>

        </div>
    );
}