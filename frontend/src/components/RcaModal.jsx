import HumanRcaBox from "./HumanRcaBox";

/**
 * RcaModal
 * Props:
 *   issueKey   – string
 *   data       – RCA API response object | null
 *   loading    – bool
 *   error      – string | null
 *   onClose    – () => void
 *   onSubmitHuman – async (rootCause, affected) => void
 */
export default function RcaModal({ issueKey, data, loading, error, onClose, onSubmitHuman }) {

    // click-outside closes
    function handleBackdrop(e) {
        if (e.target === e.currentTarget) onClose();
    }

    // confidence → tailwind colour classes (matches original dashboard JS palette)
    const confClass = {
        HIGH: "text-green  border-green/20  bg-green/5",
        MEDIUM: "text-yellow border-yellow/20 bg-yellow/5",
        LOW: "text-red    border-red/20    bg-red/5",
        HUMAN: "text-blue-300 border-blue-400/20 bg-blue-400/5",
    }[data?.confidence] ?? "text-muted border-muted/20 bg-white/5";

    const isLow = data?.confidence === "LOW" || data?.needs_human_review;
    const isHumanSaved = data?.source === "human_override";

    return (
        <div
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 animate-fadeIn"
            onClick={handleBackdrop}
        >
            <div className="bg-surface border border-purple/15 rounded-2xl w-[640px] max-h-[90vh] overflow-auto relative shadow-2xl animate-slideUp">

                {/* ── HEADER ── */}
                <div className="flex items-center justify-between px-6 py-4 bg-surface2 border-b border-purple/15 sticky top-0 z-10">
                    <div>
                        <h2 className="font-bold text-red">🔍 Copilot RCA</h2>
                        <p className="font-mono text-muted text-xs mt-0.5">Ticket: {issueKey}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="font-mono text-muted hover:text-slate-200 text-lg w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 transition-colors"
                    >
                        ✕
                    </button>
                </div>

                {/* ── BODY ── */}
                <div className="p-6 space-y-5">

                    {/* LOADING */}
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-10 gap-3">
                            <svg className="animate-spin h-6 w-6 text-purple" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                            </svg>
                            <span className="font-mono text-muted text-xs">Analysing incident…</span>
                        </div>
                    )}

                    {/* ERROR */}
                    {!loading && error && (
                        <div className="font-mono text-center py-8 text-sm">
                            <div className="text-3xl mb-3">❌</div>
                            <div className="text-red">{error}</div>
                        </div>
                    )}

                    {/* RESULT */}
                    {!loading && !error && data && (
                        <>
                            {/* TOP ROW — confidence + source badges */}
                            <div className="flex items-center gap-2 flex-wrap">
                                <span className={`font-mono text-xs px-3 py-1 rounded-full border ${confClass} font-semibold`}>
                                    {data.confidence || "LOW"}
                                </span>
                                <span className="font-mono text-xs text-muted">{data.confidence_label || ""}</span>

                                <div className="ml-auto flex items-center gap-2">
                                    {data.cached && (
                                        <span className="font-mono text-xs px-2.5 py-0.5 rounded-full border border-purple/20 bg-purple/10 text-purple">
                                            ⚡ Cached
                                        </span>
                                    )}
                                    {isHumanSaved ? (
                                        <span className="font-mono text-xs px-2.5 py-0.5 rounded-full border border-blue-400/20 bg-blue-400/5 text-blue-300">
                                            ✍️ Human Verified
                                        </span>
                                    ) : data.source === "matched" ? (
                                        <span className="font-mono text-xs px-2.5 py-0.5 rounded-full border border-green/20 bg-green/5 text-green">
                                            🔗 Matched
                                        </span>
                                    ) : (
                                        <span className="font-mono text-xs px-2.5 py-0.5 rounded-full border border-yellow/20 bg-yellow/5 text-yellow">
                                            ✨ Generated
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* MATCHED FROM banner */}
                            {data.source === "matched" && data.matched_from && (
                                <div className="bg-surface2 border border-green/15 rounded-xl px-4 py-3 flex items-start gap-3">
                                    <span className="text-green text-base flex-shrink-0">🔗</span>
                                    <div>
                                        <span className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block mb-1">
                                            RCA sourced from past ticket
                                        </span>
                                        <span className="font-mono text-xs text-green font-bold">{data.matched_from}</span>
                                        {data.matched_summary && (
                                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">{data.matched_summary}</p>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* SUMMARY line */}
                            <div className="font-mono text-xs text-muted italic">{data.summary || ""}</div>

                            {/* ROOT CAUSE */}
                            <div className="bg-surface2 border border-purple/10 rounded-xl p-4">
                                <span className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block mb-2">Root Cause</span>
                                <p className="text-sm leading-relaxed text-slate-200">{data.root_cause || "–"}</p>
                            </div>

                            {/* AFFECTED COMPONENT */}
                            <div className="bg-surface2 border border-purple/10 rounded-xl p-4">
                                <span className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block mb-2">Affected Component</span>
                                <p className="text-sm text-yellow font-semibold">{data.affected || "–"}</p>
                            </div>

                            {/* RESOLUTION STEPS */}
                            <div className="bg-surface2 border border-purple/10 rounded-xl p-4">
                                <span className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block mb-3">Resolution Steps</span>
                                <ol className="space-y-2">
                                    {(data.steps || []).map((step, i) => (
                                        <li key={i} className="flex items-start gap-3 text-sm">
                                            <span className="font-mono text-purple font-bold flex-shrink-0">{i + 1}.</span>
                                            <span className="text-slate-200 leading-relaxed">{step}</span>
                                        </li>
                                    ))}
                                </ol>
                            </div>

                            {/* HUMAN INTERVENTION BOX — LOW confidence only, before save */}
                            {isLow && !isHumanSaved && (
                                <HumanRcaBox
                                    issueKey={issueKey}
                                    aiAffected={data.affected || ""}
                                    onSubmit={(rootCause, affected) =>
                                        onSubmitHuman(issueKey, { rootCause, affected })
                                    }
                                />
                            )}

                            {/* HUMAN VERIFIED BANNER — after save */}
                            {isHumanSaved && (
                                <div className="animate-slideUp bg-blue-400/5 border border-blue-400/20 rounded-xl px-4 py-3 flex items-center gap-3">
                                    <span className="text-blue-300 text-base flex-shrink-0">✍️</span>
                                    <p className="font-mono text-xs text-blue-300 leading-relaxed">
                                        This RCA was written and verified by a human reviewer. It has been stored
                                        in the database and will be used for future incident matching.
                                    </p>
                                </div>
                            )}
                        </>
                    )}

                </div>
            </div>
        </div>
    );
}