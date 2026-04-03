import type { AlertRecord, SuggestedAction } from "./api";

export type UiActionType = "block_sku" | "block_listing" | "mark_review";

export type UiActionDefinition = {
  type: UiActionType;
  label: string;
  apiAction: SuggestedAction;
  disabled?: boolean;
  helper?: string;
};

export type AlertSelection = {
  selectedAlertId: number | null;
};

export type AlertSummaryView = AlertRecord;
