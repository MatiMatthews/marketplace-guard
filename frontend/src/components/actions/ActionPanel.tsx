import { useState } from "react";
import { buildUiActions } from "../../lib/mappers";
import type { AlertDetailResponse } from "../../types/api";
import { useAlertActions } from "../../hooks/useAlertActions";
import Panel from "../layout/Panel";
import ActionButton from "./ActionButton";
import ApprovalModal from "./ApprovalModal";

type ActionPanelProps = {
  detail: AlertDetailResponse | null;
  requestedBy: string;
  onCompleted: () => Promise<void>;
};

export default function ActionPanel({
  detail,
  requestedBy,
  onCompleted,
}: ActionPanelProps) {
  const { executeAction, pendingAction, error, setError } = useAlertActions(requestedBy);
  const [approvalAction, setApprovalAction] = useState<string | null>(null);
  const [approvalLoading, setApprovalLoading] = useState(false);

  async function runAction(actionType: "simulate_block_sku" | "mark_review") {
    if (!detail) {
      return;
    }

    try {
      const result = await executeAction(detail.alert.id, actionType, false);
      if (result.kind === "approval_required") {
        setApprovalAction(actionType);
        return;
      }
      await onCompleted();
    } catch {
      return;
    }
  }

  async function confirmApproval() {
    if (!detail || !approvalAction) {
      return;
    }

    setApprovalLoading(true);
    try {
      await executeAction(detail.alert.id, approvalAction as "simulate_block_sku", true);
      setApprovalAction(null);
      await onCompleted();
    } catch {
      return;
    } finally {
      setApprovalLoading(false);
    }
  }

  const actions = detail ? buildUiActions(detail) : [];

  return (
    <>
      <Panel title="Action Panel" subtitle="Acciones operativas">
        {!detail ? (
          <p className="text-sm text-muted">
            Selecciona una alerta para ejecutar acciones.
          </p>
        ) : (
          <div className="space-y-3.5">
            {actions.map((action) => (
              <div key={action.type}>
                <ActionButton
                  disabled={Boolean(action.disabled)}
                  label={action.label}
                  loading={pendingAction === action.apiAction}
                  onClick={() => void runAction(action.apiAction as "simulate_block_sku" | "mark_review")}
                  tone={action.type === "block_sku" ? "primary" : "secondary"}
                />
                {action.helper ? (
                  <p className="mt-1.5 px-1 text-xs leading-5 text-muted">{action.helper}</p>
                ) : null}
              </div>
            ))}

            {error ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">
                {error}
              </div>
            ) : null}
          </div>
        )}
      </Panel>

      <ApprovalModal
        loading={approvalLoading}
        onClose={() => {
          setApprovalAction(null);
          setError(null);
        }}
        onConfirm={() => void confirmApproval()}
        open={approvalAction !== null}
      />
    </>
  );
}
