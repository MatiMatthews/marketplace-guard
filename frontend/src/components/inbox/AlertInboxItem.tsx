import { formatNumber } from "../../lib/format";
import { getAlertTypeLabel, getChannelLabel } from "../../lib/mappers";
import type { AlertRecord } from "../../types/api";
import ActionChip from "./ActionChip";
import PriorityBadge from "./PriorityBadge";

type AlertInboxItemProps = {
  alert: AlertRecord;
  selected: boolean;
  onSelect: (alertId: number) => void;
};

export default function AlertInboxItem({
  alert,
  selected,
  onSelect,
}: AlertInboxItemProps) {
  const selectedClasses = selected
    ? "border-slate-900 bg-[linear-gradient(180deg,#0f172a_0%,#111c31_100%)] text-white shadow-[0_16px_34px_rgba(15,23,42,0.18)]"
    : "border-slate-200/80 bg-white hover:border-slate-300 hover:bg-slate-50/70 shadow-[0_6px_18px_rgba(15,23,42,0.04)]";

  return (
    <button
      className={`w-full rounded-2xl border p-4 text-left transition duration-150 ${selectedClasses}`}
      onClick={() => onSelect(alert.id)}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className={`truncate text-base font-semibold ${selected ? "text-white" : "text-slate-950"}`}>
            {alert.sku}
          </p>
          <p className={`mt-1 text-sm ${selected ? "text-slate-300" : "text-slate-500"}`}>
            {getChannelLabel(alert)}
          </p>
        </div>
        <PriorityBadge value={alert.priority_score} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <span
          className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
            selected
              ? "border-slate-700 bg-slate-800 text-slate-100"
              : "border-slate-200 bg-slate-100 text-slate-600"
          }`}
        >
          {getAlertTypeLabel(alert.alert_type)}
        </span>
        <ActionChip action={alert.suggested_action} />
      </div>

      <div
        className={`mt-4 grid grid-cols-[1.2fr_0.8fr] gap-3 rounded-xl border px-3 py-3 text-xs ${
          selected
            ? "border-slate-800 bg-slate-800/80 text-slate-200"
            : "border-slate-200 bg-slate-50/80 text-slate-500"
        }`}
      >
        <div className="min-w-0">
          <p className="uppercase tracking-[0.16em]">Pérdida estimada</p>
          <p className={`mt-1 truncate text-base font-semibold ${selected ? "text-white" : "text-slate-950"}`}>
            {formatNumber(alert.estimated_loss)}
          </p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.14em]">{alert.currency || "CLP"}</p>
        </div>
        <div className="text-right">
          <p className="uppercase tracking-[0.16em]">Impacto</p>
          <p className={`mt-1 text-base font-semibold ${selected ? "text-white" : "text-slate-950"}`}>
            {formatNumber(alert.impact_score)}
          </p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.14em]">score</p>
        </div>
      </div>
    </button>
  );
}
