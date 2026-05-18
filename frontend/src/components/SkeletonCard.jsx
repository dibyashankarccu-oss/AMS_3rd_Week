export default function SkeletonCard() {
  return (
    <div className="bg-surface border border-purple/15 rounded-2xl p-5 mb-6">
      <div className="h-3.5 rounded-lg bg-surface2 w-2/5 mb-3 animate-shimmer" />
      <div className="h-3.5 rounded-lg bg-surface2 w-full mb-2 animate-shimmer" />
      <div className="h-3.5 rounded-lg bg-surface2 w-4/5 mb-2 animate-shimmer" />
      <div className="h-3.5 rounded-lg bg-surface2 w-11/12 animate-shimmer" />
    </div>
  );
}