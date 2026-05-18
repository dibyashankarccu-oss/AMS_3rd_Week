export default function StatusBar({ state, text, time }) {
  const dotColor = {
    running: "#facc15",
    done:    "#4ade80",
    error:   "#f87171",
  }[state] || "#64748b";

  return (
    <div className="font-mono flex items-center gap-3 bg-surface border border-purple/15 rounded-xl px-5 py-3.5 mb-8 text-xs">
      <div
        className={`w-2 h-2 rounded-full flex-shrink-0 ${state === "running" ? "animate-pulse2" : ""}`}
        style={{ background: dotColor, boxShadow: `0 0 8px ${dotColor}` }}
      />
      <span className="flex-1 text-slate-200">{text}</span>
      <span className="text-muted text-[0.7rem]">{time}</span>
    </div>
  );
}