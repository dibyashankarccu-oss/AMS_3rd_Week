import { useState } from "react";

export default function RunbookSection({ icon, title, count, children, delay = 0, rightSlot }) {
  const [open, setOpen] = useState(true);

  return (
    <div
      className="bg-surface border border-purple/15 rounded-2xl overflow-hidden mb-6 animate-slideUp"
      style={{ animationDelay: `${delay}s` }}
    >
      {/* HEAD */}
      <div
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between px-5 py-4 bg-surface2 border-b border-purple/15 cursor-pointer select-none"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 flex items-center justify-center bg-purple/25 border border-purple/15 rounded-lg text-lg">
            {icon}
          </div>
          <span className="font-mono text-xs font-bold tracking-widest uppercase text-purple">
            {title}
          </span>
          {count && (
            <span className="font-mono text-[0.7rem] text-muted bg-white/5 px-2 py-0.5 rounded-full">
              {count}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {rightSlot}
          <span
            className="text-muted text-xs transition-transform duration-200 inline-block"
            style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
          >
            ▼
          </span>
        </div>
      </div>

      {/* BODY */}
      {open && <div className="p-5">{children}</div>}
    </div>
  );
}