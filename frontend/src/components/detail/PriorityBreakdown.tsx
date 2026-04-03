import { formatNumber, formatPriority } from "../../lib/format";
import type { AlertRecord } from "../../types/api";
import PriorityBadge from "../inbox/PriorityBadge";

type PriorityBreakdownProps = {
  alert: AlertRecord;
};

function BreakdownRow({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/90 px-4 py-3">
      <span className="text-sm font-medium text-slate-600">{label}</span>
      <span className="text-sm font-semibold text-slate-950">{formatNumber(value)}</span>
    </div>
  );
}

export default function PriorityBreakdown({ alert }: PriorityBreakdownProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="panel-title">Priority Score</p>
          <p className="mt-2 text-4xl font-semibold tracking-[-0.04em] text-slate-950">
            {formatPriority(alert.priority_score)}
          </p>
        </div>
        <PriorityBadge value={alert.priority_score} />
      </div>

      <div className="mt-5 space-y-2.5">
        <BreakdownRow
          label="Pérdida"
          value={alert.estimated_loss_component}
        />
        <BreakdownRow
          label="Margen"
          value={alert.negative_margin_component}
        />
        <BreakdownRow
          label="Volumen"
          value={alert.volume_component}
        />
      </div>
    </div>
  );
}
