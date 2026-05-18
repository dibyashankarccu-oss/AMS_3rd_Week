import { useState, useCallback } from "react";
import { apiRequest } from "../api/apiClient";

export function useTickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [childModal, setChildModal] = useState(null);
  const [deleteModal, setDeleteModal] = useState(null); // { issueKey }
  const [mergeModal, setMergeModal] = useState(null);
  const [mergeTickets, setMergeTickets] = useState([]);

  // ── LOAD ──
  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest("/tickets");
      const all =
        Array.isArray(res) ? res :
          Array.isArray(res?.tickets) ? res.tickets :
            Array.isArray(res?.data) ? res.data : [];
      setTickets(all.filter(t => !t.parent_ticket_key && !t.child_key));
    } catch (err) {
      console.error("❌ loadTickets error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateStatus = useCallback(async (issueKey, value) => {
    if (value !== "Completed") return;

    const res = await apiRequest(
      `/tickets/${issueKey}/complete`,
      "PUT"
    );

    // ── HANDLE WARNING (NEW FLOW) ──
    if (res?.requires_confirmation) {
      setConfirmModal({
        issueKey,
        openChildren: res.open_children || [],
      });
      return;
    }

    if (res?.error) {
      console.error("❌ Status update failed:", res.message);
      loadTickets();
      return;
    }

    localStorage.removeItem(`esc_${issueKey}`);
    setTimeout(() => loadTickets(), 500);
  }, [loadTickets]);

  
  // ── COMPLETE ONLY SINGLE TICKET ──
  const completeSingle = useCallback(

    async (issueKey) => {

      try {

        const res = await apiRequest(
          `/tickets/${issueKey}/complete-single`,
          "PUT"
        );

        if (
          !res ||
          res.type === "error"
        ) {

          console.error(
            res?.message
          );

          return;
        }

        await loadTickets();

      }

      catch (err) {

        console.error(
          "completeSingle:",
          err
        );

      }

    },

    [loadTickets]

  );

  // ── OPEN DELETE OPTIONS MODAL (matches showDeleteOptions in tickets.js) ──
  const openDeleteModal = useCallback((issueKey) => {
    setDeleteModal({ issueKey });
  }, []);

  // ── DELETE PARENT + ALL CHILDREN (cascade) ──
  const deleteParentCascade = useCallback(async (issueKey) => {
    const res = await apiRequest(`/tickets/${issueKey}`, "DELETE");
    if (res?.error) { console.error("❌ Cascade delete failed:", res.message); return; }
    setDeleteModal(null);
    loadTickets();
  }, [loadTickets]);

  // ── DELETE PARENT ONLY ──
  const deleteParentOnly = useCallback(async (issueKey) => {
    const res = await apiRequest(`/tickets/${issueKey}/parent-only`, "DELETE");
    if (res?.error) { console.error("❌ Parent delete failed:", res.message); return; }
    setDeleteModal(null);
    loadTickets();
  }, [loadTickets]);

  // ── DELETE SINGLE CHILD ──
  const deleteSingleChild = useCallback(async (issueKey) => {
    const res = await apiRequest(`/tickets/child/${issueKey}`, "DELETE");
    if (res?.error) { console.error("❌ Child delete failed:", res.message); return; }
    setChildModal(null);
    loadTickets();
  }, [loadTickets]);

  // ── OPEN CHILD MODAL ──
  const openChildModal = useCallback(async (parentKey) => {
    const res = await apiRequest("/tickets");
    const all =
      Array.isArray(res) ? res :
        Array.isArray(res?.tickets) ? res.tickets :
          Array.isArray(res?.data) ? res.data : [];
    const children = all.filter(t => t.parent_ticket_key === parentKey);
    setChildModal({ parentKey, children });
  }, []);

  // ── DETACH CHILD ──
  const detachChild = useCallback(async (issueKey) => {
    const res = await apiRequest(`/tickets/${issueKey}/detach`, "PUT");
    if (res?.error) { console.error("❌ Detach failed:", res.message); return; }
    setChildModal(null);
    loadTickets();
  }, [loadTickets]);

  // ── OPEN MERGE MODAL ──
  const openMergeModal = useCallback(async (targetKey) => {
    const res = await apiRequest("/tickets");
    const all =
      Array.isArray(res) ? res :
        Array.isArray(res?.tickets) ? res.tickets :
          Array.isArray(res?.data) ? res.data : [];
    const parents = all.filter(t =>
      !t.parent_ticket_key && !t.child_key && t.issue_key !== targetKey
    );
    setMergeTickets(parents);
    setMergeModal({ targetKey });
  }, []);

  // ── EXECUTE MERGE ──
  const executeMerge = useCallback(async (targetKey, sourceKey) => {
    const res = await apiRequest("/tickets/merge", "POST", {
      target_parent_key: targetKey,
      source_parent_keys: [sourceKey],
    });
    console.log("Merge result:", res);
    setMergeModal(null);
    loadTickets();
  }, [loadTickets]);

  return {
    tickets, loading, loadTickets,
    updateStatus, completeSingle,
    // delete
    deleteModal, openDeleteModal, closeDeleteModal: () => setDeleteModal(null),
    deleteParentCascade, deleteParentOnly, deleteSingleChild,
    // child modal
    childModal, openChildModal, closeChildModal: () => setChildModal(null), detachChild,
    // merge modal
    mergeModal, mergeTickets, openMergeModal, closeMergeModal: () => setMergeModal(null), executeMerge,
  };
}