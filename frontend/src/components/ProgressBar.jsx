export default function ProgressBar({ pct }) {
  return (
    <div className="h-1 bg-white/5 rounded-full mb-6 overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-purpled to-purple transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}