import { useState } from "react";
import { apiRequest } from "../api/apiClient";

export default function MergeModal({ targetKey, onClose, onMerge }) {
  const [jiraId, setJiraId] = useState("");
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [merging, setMerging] = useState(false); // NEW

  const searchTicket = async () => {
    if (!jiraId.trim()) return;

    setLoading(true);

    try {
      const res = await apiRequest(`/tickets/search/${jiraId.trim()}`);
      console.log("Search:", res);

      if (res?.type === "error" || !res?.parent) {
        alert("Ticket not found");
        setTicket(null);
        return;
      }

      // allow only parent tickets
      if (res.mode !== "parent-view") {
        alert("Only parent tickets can be merged");
        setTicket(null);
        return;
      }

      // prevent self merge
      if (res.parent.issue_key === targetKey) {
        alert("Cannot merge into same ticket");
        setTicket(null);
        return;
      }

      setTicket(res.parent);
    } catch (err) {
      console.log("search error:", err);
      setTicket(null);
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async () => {
    if (!ticket) return;

    try {
      setMerging(true);
      await onMerge(targetKey, ticket.issue_key);
      setMerging(false);
      onClose();
    } catch (err) {
      console.error("Merge error:", err);
      alert("Failed to merge ticket");
      setMerging(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-surface border border-purple/20 rounded-2xl p-6 w-[520px]">
        <div className="flex justify-between mb-5">
          <div>
            <h2 className="font-bold text-lg">Merge Tickets</h2>
            <p className="text-xs text-muted">Target: {targetKey}</p>
          </div>
          <button onClick={onClose} className="text-xl text-muted">
            ✕
          </button>
        </div>

        <input
          value={jiraId}
          onChange={(e) => setJiraId(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && searchTicket()}
          placeholder="Enter Jira ID (TP-123)"
          className="w-full px-3 py-3 rounded-xl bg-surface2 border border-purple/20 outline-none"
        />

        <button
          onClick={searchTicket}
          className="w-full mt-3 bg-purple hover:bg-purpled text-black font-bold rounded-xl py-2"
        >
          {loading ? "Searching..." : "Search"}
        </button>

        {ticket && (
          <div className="mt-5 border border-purple/20 rounded-xl p-4 space-y-3">
            <div className="font-mono text-yellow font-bold">{ticket.issue_key}</div>
            <div className="text-sm text-slate-300">{ticket.summary}</div>

            <button
              onClick={handleMerge}
              disabled={merging}
              className={`w-full rounded-xl py-2 font-bold ${
                merging ? "bg-gray-500 cursor-not-allowed" : "bg-green/20 hover:bg-green/30"
              }`}
            >
              {merging ? "Merging..." : "Confirm Merge"}
            </button>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full mt-4 bg-red-500/20 hover:bg-red-500/30 rounded-xl py-2"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}