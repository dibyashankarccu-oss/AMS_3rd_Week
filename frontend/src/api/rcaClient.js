import { apiRequest } from "./apiClient";

/** Fetch (or generate) the RCA for a ticket */
export function fetchRca(issueKey) {
  return apiRequest(`/tickets/${issueKey}/rca`);
}

/** Submit a human-written root cause override */
export function submitHumanRca(issueKey, { rootCause, affected }) {
  return apiRequest(`/tickets/${issueKey}/rca/human`, "POST", {
    root_cause: rootCause,
    affected:   affected || undefined,
  });
}

/** Submit clarification answers (existing HITL flow) */
export function submitClarification(issueKey, { questions, answers }) {
  return apiRequest(`/tickets/${issueKey}/rca/clarify`, "POST", {
    questions,
    answers,
  });
}