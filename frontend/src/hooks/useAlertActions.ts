import { useState } from "react";
import { ApiError, runAlertAction } from "../lib/api";
import type { SuggestedAction } from "../types/api";

type ActionResult =
  | { kind: "success" }
  | { kind: "approval_required"; detail: Record<string, unknown> };

export function useAlertActions(requestedBy: string) {
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function executeAction(
    alertId: number,
    actionType: SuggestedAction,
    approved = false,
  ): Promise<ActionResult> {
    setPendingAction(actionType);
    setError(null);
    try {
      await runAlertAction(alertId, {
        action_type: actionType,
        requested_by: requestedBy,
        approved,
      });
      return { kind: "success" };
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const payload =
          typeof err.payload === "object" && err.payload !== null
            ? (err.payload as { detail?: unknown }).detail
            : null;
        if (payload && typeof payload === "object") {
          return { kind: "approval_required", detail: payload as Record<string, unknown> };
        }
      }

      setError(err instanceof Error ? err.message : "No se pudo ejecutar la acción.");
      throw err;
    } finally {
      setPendingAction(null);
    }
  }

  return {
    pendingAction,
    error,
    setError,
    executeAction,
  };
}
