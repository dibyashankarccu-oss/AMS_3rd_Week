import { useState } from "react";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
      className="font-mono text-[0.7rem] text-muted bg-white/5 px-2.5 py-1 rounded-md hover:text-slate-200 hover:bg-white/10 transition-all border-none cursor-pointer"
    >
      {copied ? "✓ Copied" : "Copy"}
    </button>
  );
}

export default function ChecklistItem({ item, index, checked, onToggle }) {
  const hasCmd = item.cmd && item.cmd.trim();

  return (
    <div
      onClick={() => onToggle(index)}
      className={`flex items-start gap-3 px-4 py-3 rounded-xl cursor-pointer border transition-all ${
        checked
          ? "bg-green/5 border-green/20"
          : "bg-surface2 border-transparent hover:border-purple/15"
      }`}
    >
      {/* Checkbox */}
      <div className={`w-[18px] h-[18px] min-w-[18px] rounded-[5px] border-2 flex items-center justify-center mt-0.5 flex-shrink-0 transition-all ${
        checked ? "bg-green border-green" : "border-muted"
      }`}>
        {checked && <span className="text-black text-[11px] font-black">✓</span>}
      </div>

      {/* Step + command */}
      <div className="flex-1 min-w-0">
        <span className={`text-sm leading-relaxed ${checked ? "text-muted line-through" : "text-slate-200"}`}>
          {item.step}
        </span>

        {hasCmd && (
          <div
            onClick={e => e.stopPropagation()}
            className="mt-2 border border-purple/15 rounded-lg overflow-hidden hover:border-purple/30 transition-colors"
          >
            <div className="flex items-center justify-between px-3 py-1.5 bg-surface2">
              <span className="font-mono text-[0.7rem] text-muted">$ shell</span>
              <CopyButton text={item.cmd} />
            </div>
            <div className="px-3 py-2.5 bg-[#0a0a10] font-mono text-[0.78rem] text-violet-300 whitespace-pre-wrap break-all leading-relaxed">
              {item.cmd}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}