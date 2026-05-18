import StatusBadge from "./StatusBadge";
import FieldLabel from "./FieldLabel";
import { useState } from "react";
import { apiRequest } from "../api/apiClient";

export default function ChildModal({ parentKey, children, onClose, onDetach, updateStatus, completeSingle }) {
  const [showCompletePopup, setShowCompletePopup] = useState(false);
  const [selectedChild, setSelectedChild] = useState(null);
  const [creatingChild, setCreatingChild] = useState(null);

  async function completeAllChildren(issueKey) {

    try {

      console.log(
        "calling complete children:",
        issueKey
      );

      const res = await apiRequest(
        `/tickets/${issueKey}/complete-children`,
        "PUT"
      );

      console.log(
        "response:",
        res
      );

      if (
        res?.type === "success"
      ) {

        setShowCompletePopup(false);
        setSelectedChild(null);

        window.location.reload();
      }

    }

    catch (e) {

      console.error(
        "completeAllChildren failed:",
        e
      );

    }

  }

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-surface border border-purple/15 rounded-2xl w-[620px] max-h-[80vh] overflow-auto shadow-2xl animate-slideUp">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-surface2 border-b border-purple/15 sticky top-0">
          <div>
            <h2 className="font-bold text-purple">Child Tickets</h2>
            <p className="font-mono text-muted text-xs mt-0.5">Parent: {parentKey}</p>
          </div>
          <button
            onClick={onClose}
            className="font-mono text-muted hover:text-slate-200 text-lg transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {children.length === 0 ? (
            <div className="font-mono text-center py-8 text-muted text-sm">
              <div className="text-3xl mb-3">📭</div>
              <div>No child tickets found</div>
            </div>
          ) : (
            children.map(c => (
              <div key={c.issue_key} className="bg-surface2 border border-purple/10 rounded-xl p-4 space-y-2">

                {/* Child header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-yellow text-xs font-bold">{c.issue_key}</span>
                    {c.child_key && (
                      <span className="font-mono text-[0.6rem] px-2 py-0.5 rounded-full bg-yellow/10 border border-yellow/20 text-yellow">
                        {c.child_key}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">

                    <StatusBadge isCompleted={c.status === "Completed"} />

                    {c.status !== "Completed" && (
                      <select
                        className="bg-surface border border-purple/20 rounded px-2 py-1 text-xs"
                        onChange={(e) => {
                          if (e.target.value === "Completed") {
                            setSelectedChild(c);
                            setShowCompletePopup(true);
                          }
                        }}
                      >
                        <option>Open</option>
                        <option>Completed</option>
                      </select>
                    )}

                  </div>
                </div>

                {/* Child fields */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                  <FieldLabel label="Name"><span>{c.name || "-"}</span></FieldLabel>
                  <FieldLabel label="Email"><span>{c.email || "-"}</span></FieldLabel>
                  <FieldLabel label="Summary" className="col-span-2"><span>{c.summary || "-"}</span></FieldLabel>
                  <FieldLabel label="Description" className="col-span-2">
                    <span className="text-slate-300 leading-relaxed">{c.description || "-"}</span>
                  </FieldLabel>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    onClick={() => window.open(`${import.meta.env.VITE_JIRA_BASE_URL}/browse/${c.issue_key}`, "_blank")}
                    className="bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-400 text-[0.65rem] font-bold py-1.5 px-3 rounded-lg font-mono transition-all"
                  >
                    🔗 Open in Jira
                  </button>

                  <button
                    onClick={async () => {
                      setCreatingChild(c.issue_key);       // start creating for this child
                      await onDetach(c.issue_key);
                      setCreatingChild(null);               // done creating
                    }}
                    disabled={creatingChild === c.issue_key}
                    className={`border rounded-lg text-[0.65rem] font-bold py-1.5 px-3 font-mono transition-all ${creatingChild === c.issue_key
                      ? "bg-gray-500 text-gray-200 cursor-not-allowed"
                      : "bg-green/10 hover:bg-green/20 border-green/20 text-green"
                      }`}
                  >
                    {creatingChild === c.issue_key ? "Creating..." : "➕ Create New Ticket"}
                  </button>
                </div>

              </div>
            ))
          )}
        </div>

      </div>

      {/* Completion Popup */}
      {showCompletePopup && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[999]">
          <div className="bg-surface border border-purple/20 rounded-xl p-6 w-[420px]">
            <h3 className="font-bold text-lg mb-4">Completion Option</h3>
            <div className="space-y-3">
              <button
                className="w-full bg-green/20 hover:bg-green/30 py-2 rounded"
                onClick={async () => {
                  await completeSingle(selectedChild.issue_key);
                  setShowCompletePopup(false);
                }}
              >
                Mark only this ticket as completed
              </button>
              <button
                onClick={async () => {
                  console.log("BUTTON CLICKED");

                  if (!selectedChild) {
                    console.log("selected child missing");
                    return;
                  }

                  await completeAllChildren(selectedChild.issue_key);
                }}
                disabled={!selectedChild}
                className="
    w-full
    px-4 py-2
    bg-yellow text-black font-semibold
    rounded-lg
    shadow-md hover:shadow-lg
    transition-all duration-200
    active:scale-[0.98]
    focus:outline-none focus:ring-2 focus:ring-yellow/40 focus:ring-offset-2
    disabled:opacity-40 disabled:cursor-not-allowed
  "
              >
                Complete all child tickets
              </button>
              <button
                className="w-full bg-red-500/20 hover:bg-red-500/30 py-2 rounded"
                onClick={() => setShowCompletePopup(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}