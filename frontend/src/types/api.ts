export type AlertType =
  | "broken_margin"
  | "price_inconsistency"
  | "promo_margin_break";

export type SuggestedAction = "simulate_block_sku" | "mark_review" | "notify";

export type ApiEnvelope<T> = {
  ok: boolean;
  data: T;
  meta?: Record<string, unknown>;
};

export type ApiErrorPayload = {
  detail?: string | Record<string, unknown>;
};

export type AlertRecord = {
  id: number;
  alert_type: AlertType;
  severity: string;
  status: string;
  product_id: number;
  listing_id: number | null;
  currency: string | null;
  sku: string;
  product_name: string;
  channel_code: string | null;
  channel_name: string | null;
  title: string;
  explanation: string;
  estimated_loss: number;
  impact_score: number;
  priority_score: number;
  estimated_loss_component: number;
  negative_margin_component: number;
  volume_component: number;
  suggested_action: SuggestedAction;
  evidence: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type MarginResult = {
  listing_id: number;
  product_id: number;
  sku: string;
  channel_code: string;
  final_price: number;
  fee_amount: number;
  shipping_subsidy_amount: number;
  unit_cost: number;
  handling_cost: number;
  min_margin_amount: number;
  net_revenue: number;
  margin_value: number;
  threshold_value: number;
  margin_gap: number;
  margin_ok: boolean;
  promotion_id: number | null;
  promotion_name: string | null;
};

export type TimelineEvent = {
  event_type: string;
  timestamp: string;
  title: string;
  details: Record<string, unknown>;
};

export type ActionRunRecord = {
  id: number;
  alert_id: number;
  action_type: string;
  target_type: string;
  target_id: string;
  status: string;
  approval_status: string;
  requested_by: string;
  requested_at: string;
  executed_at: string | null;
  result: Record<string, unknown>;
};

export type AlertDetailResponse = {
  alert: AlertRecord;
  pricing: MarginResult | null;
  timeline: TimelineEvent[];
  action_runs: ActionRunRecord[];
};

export type SimulateRunResponse = {
  session_id: string;
  alerts_created: number;
  alerts: AlertRecord[];
  summary: string;
};

export type AlertActionRequest = {
  action_type: SuggestedAction;
  requested_by: string;
  approved: boolean;
};

export type AlertActionResponse =
  | ActionRunRecord
  | {
      session_id: string;
      action_run_id: number | null;
      summary: string;
      alert: AlertDetailResponse | null;
    };
