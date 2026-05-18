export default function StatusBadge({ isCompleted }) {
  return (
    <span className={`font-mono text-xs px-2.5 py-0.5 rounded-full border ${
      isCompleted
        ? "text-green border-green/20 bg-green/5"
        : "text-yellow border-yellow/20 bg-yellow/5"
    }`}>
      {isCompleted ? "✔ Completed" : "● Open"}
    </span>
  );
}