import { useState, useCallback } from "react";
import { fetchRca, submitHumanRca } from "../api/rcaClient";

export function useRca() {
  const [rcaModal,  setRcaModal]  = useState(null); // null | { issueKey }
  const [rcaData,   setRcaData]   = useState(null); // the API response
  const [rcaLoading, setRcaLoading] = useState(false);
  const [rcaError,  setRcaError]  = useState(null);

  // ── OPEN: fetch RCA and open modal ──
  const openRcaModal = useCallback(async (issueKey) => {
    setRcaModal({ issueKey });
    setRcaData(null);
    setRcaError(null);
    setRcaLoading(true);

    try {
      const res = await fetchRca(issueKey);
      if (!res || res.error || res.type === "error") {
        setRcaError(res?.detail || res?.message || "Failed to load RCA");
      } else {
        setRcaData(res);
      }
    } catch (err) {
      setRcaError(err.message || "Unexpected error");
    } finally {
      setRcaLoading(false);
    }
  }, []);

  // ── CLOSE ──
  const closeRcaModal = useCallback(() => {
    setRcaModal(null);
    setRcaData(null);
    setRcaError(null);
    setRcaLoading(false);
  }, []);

  // ── SUBMIT HUMAN OVERRIDE ──
  const submitHuman = useCallback(async (issueKey, { rootCause, affected }) => {
    const res = await submitHumanRca(issueKey, { rootCause, affected });
    if (!res || res.error) {
      throw new Error(res?.message || "Save failed");
    }
    // replace the displayed result with the saved human RCA
    setRcaData(res);
    return res;
  }, []);

  return {
    rcaModal, rcaData, rcaLoading, rcaError,
    openRcaModal, closeRcaModal, submitHuman,
  };
}