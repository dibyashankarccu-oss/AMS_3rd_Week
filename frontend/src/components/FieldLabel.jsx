export default function FieldLabel({ label, children, className = "" }) {
  return (
    <div className={className}>
      <span className="font-mono text-[0.6rem] text-muted uppercase tracking-widest block mb-0.5">
        {label}
      </span>
      {children}
    </div>
  );
}