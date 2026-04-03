import { formatCurrencyValue, formatNumber } from "../../lib/format";
import type { AlertDetailResponse } from "../../types/api";

type PricingSummaryProps = {
  detail: AlertDetailResponse;
};

type MetricCardProps = {
  label: string;
  value: string;
  tone?: "default" | "danger";
};

function MetricCard({ label, value, tone = "default" }: MetricCardProps) {
  return (
    <div
      className={`rounded-2xl border px-4 py-4 shadow-sm ${
        tone === "danger"
          ? "border-rose-200 bg-[linear-gradient(180deg,#fff6f7_0%,#fff1f2_100%)]"
          : "border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]"
      }`}
    >
      <p className="metric-label">{label}</p>
      <p className={`mt-3 text-[1.35rem] font-semibold tracking-[-0.03em] ${tone === "danger" ? "text-rose-700" : "text-slate-950"}`}>
        {value}
      </p>
    </div>
  );
}

export default function PricingSummary({ detail }: PricingSummaryProps) {
  const pricing = detail.pricing;
  const currency = detail.alert.currency || "CLP";
  const costTotal =
    pricing ? pricing.unit_cost + pricing.handling_cost : null;

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Costo"
          value={
            costTotal === null
              ? "N/A"
              : formatCurrencyValue(costTotal, currency)
          }
        />
        <MetricCard
          label="Precio"
          value={
            pricing
              ? formatCurrencyValue(pricing.final_price, currency)
              : "N/A"
          }
        />
        <MetricCard
          label="Margen"
          tone={pricing && pricing.margin_value < 0 ? "danger" : "default"}
          value={
            pricing
              ? formatCurrencyValue(pricing.margin_value, currency)
              : "N/A"
          }
        />
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Pérdida estimada"
          value={`${formatNumber(detail.alert.estimated_loss)} ${currency}`}
        />
        <MetricCard
          label="Fee"
          value={
            pricing ? formatCurrencyValue(pricing.fee_amount, currency) : "N/A"
          }
        />
        <MetricCard
          label="Shipping"
          value={
            pricing
              ? formatCurrencyValue(pricing.shipping_subsidy_amount, currency)
              : "N/A"
          }
        />
        <MetricCard
          label="Gap vs mínimo"
          value={
            pricing ? formatCurrencyValue(pricing.margin_gap, currency) : "N/A"
          }
        />
      </div>
    </div>
  );
}
