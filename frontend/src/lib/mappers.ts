import type {
  ActionRunRecord,
  AlertDetailResponse,
  AlertRecord,
  SuggestedAction,
  TimelineEvent,
} from "../types/api";
import type { UiActionDefinition } from "../types/ui";

export function sortAlertsByPriority(alerts: AlertRecord[]) {
  return [...alerts].sort((a, b) => b.priority_score - a.priority_score);
}

export function getAlertTypeLabel(alertType: AlertRecord["alert_type"]) {
  switch (alertType) {
    case "broken_margin":
      return "Margen roto";
    case "promo_margin_break":
      return "Promo rompe margen";
    case "price_inconsistency":
      return "Precio inconsistente";
    default:
      return alertType;
  }
}

export function getSuggestedActionLabel(action: SuggestedAction) {
  switch (action) {
    case "simulate_block_sku":
      return "Bloquear";
    case "mark_review":
      return "Revisar";
    case "notify":
      return "Alertar";
    default:
      return action;
  }
}

export function getPriorityTone(priorityScore: number) {
  if (priorityScore >= 80) return "critical";
  if (priorityScore >= 60) return "high";
  if (priorityScore >= 40) return "medium";
  return "low";
}

export function getChannelLabel(alert: AlertRecord) {
  return alert.channel_name || alert.channel_code || "Multi-canal";
}

export function getListingLabel(detail: AlertDetailResponse) {
  if (detail.alert.listing_id) {
    return `#${detail.alert.listing_id}`;
  }
  const publicationId = detail.action_runs.find((item) => item.result.publication_id)?.result
    .publication_id;
  return typeof publicationId === "string" ? publicationId : "N/A";
}

export function buildUiActions(detail: AlertDetailResponse): UiActionDefinition[] {
  const hasListing = Boolean(detail.alert.listing_id);
  return [
    {
      type: "block_sku",
      label: "Bloquear SKU",
      apiAction: "simulate_block_sku",
      disabled: !hasListing,
      helper: hasListing ? undefined : "Disponible solo para alertas con listing.",
    },
    {
      type: "block_listing",
      label: "Bloquear publicación",
      apiAction: "simulate_block_sku",
      disabled: !hasListing,
      helper: hasListing ? undefined : "No hay publicación asociada.",
    },
    {
      type: "mark_review",
      label: "Marcar revisión",
      apiAction: "mark_review",
    },
  ];
}

export function buildTimeline(detail: AlertDetailResponse) {
  if (detail.timeline.length > 0) {
    return detail.timeline;
  }

  const fallback: TimelineEvent[] = [
    {
      event_type: "alert_created",
      timestamp: detail.alert.created_at,
      title: "Alerta creada",
      details: {
        severity: detail.alert.severity,
        suggested_action: detail.alert.suggested_action,
      },
    },
  ];

  detail.action_runs.forEach((actionRun) => {
    fallback.push(actionRunToTimeline(actionRun));
  });

  return fallback;
}

function actionRunToTimeline(actionRun: ActionRunRecord): TimelineEvent {
  return {
    event_type: "action_run",
    timestamp: actionRun.requested_at,
    title: `Acción ${actionRun.action_type}`,
    details: {
      status: actionRun.status,
      approval_status: actionRun.approval_status,
      requested_by: actionRun.requested_by,
    },
  };
}
