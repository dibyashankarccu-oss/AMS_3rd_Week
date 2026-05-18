import { useState, useCallback } from "react";
import { apiRequest } from "../api/apiClient";

export function useRunbook(issueKey) {
  const [status,       setStatus]       = useState({ state: "running", text: "Fetching runbook...", time: "" });
  const [progress,     setProgress]     = useState(0);
  const [data,         setData]         = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState(null);
  const [checkedItems, setCheckedItems] = useState(new Set());
  const [isReadOnly,   setIsReadOnly]   = useState(false);

  const checkBeforeResolve = useCallback(async (issueKey) => {
  const res = await apiRequest(`/tickets/${issueKey}/can-complete`);

  return {
    allowed: res.allowed,
    openChildren: res.open_children || [],
  };
}, []);
  const updateStatus = useCallback((state, text) => {
    setStatus({ state, text, time: new Date().toLocaleTimeString() });
  }, []);

  const toggleCheck = useCallback((idx) => {
    setCheckedItems(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const selectAll = useCallback((paired) => {
    setCheckedItems(prev => {
      if (prev.size === paired.length) return new Set();
      return new Set(paired.map((_, i) => i));
    });
  }, []);

  const getProgress = useCallback((totalItems) => {
    if (!totalItems) return 0;
    return Math.round((checkedItems.size / totalItems) * 100);
  }, [checkedItems]);

  const fetchRunbook = useCallback(async () => {
    if (!issueKey || issueKey === "UNKNOWN") return;

    updateStatus("running", `Fetching runbook for ${issueKey}...`);
    setLoading(true);

    // ✅ single call — ticket_status is already included in runbook response
    const runbookRes = await apiRequest(`/tickets/${issueKey}/runbook`);

    if (!runbookRes || runbookRes.error) {
      setError(runbookRes?.message || "Unknown error");
      updateStatus("error", "Failed to load runbook");
      setLoading(false);
      return;
    }

    // ✅ read ticket status directly from runbook response
    const ticketCompleted = runbookRes.ticket_status === "Completed";

    if (ticketCompleted) {
      console.log(`📦 [${issueKey}] Ticket already completed — read-only mode`);
      setIsReadOnly(true);
      updateStatus("done", `Runbook loaded for ${issueKey} (read-only)`);
    } else {
      setIsReadOnly(false);
      updateStatus("done", `Runbook loaded for ${issueKey}`);
    }

    setData(runbookRes);
    setProgress(0);
    setLoading(false);
  }, [issueKey, updateStatus]);

  const completeTicket = useCallback(async () => {
    return await apiRequest(`/tickets/${issueKey}/complete`, "PUT");
  }, [issueKey]);

  // const escalateTicket = useCallback(async () => {
  //   return await apiRequest(`/tickets/${issueKey}/escalate`, "POST");
  // }, [issueKey]);

  const createRunbook = useCallback(async (payload) => {
    return await apiRequest("/runbooks", "POST", payload);
  }, []);

  return {
    status, progress, setProgress,
    data, loading, error,
    isReadOnly,
    checkedItems, toggleCheck, selectAll, getProgress,
    fetchRunbook, completeTicket, createRunbook,checkBeforeResolve,
  };
}