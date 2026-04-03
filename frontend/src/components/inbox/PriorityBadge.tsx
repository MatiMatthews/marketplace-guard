import { getPriorityTone } from "../../lib/mappers";
import { formatPriority } from "../../lib/format";

type PriorityBadgeProps = {
  value: number;
};

const toneClasses: Record<string, string> = {
  critical: "border-rose-200 bg-rose-100 text-rose-700 shadow-[inset_0_0_0_1px_rgba(251,113,133,0.06)]",
  high: "border-amber-200 bg-amber-100 text-amber-700 shadow-[inset_0_0_0_1px_rgba(245,158,11,0.06)]",
  medium: "border-yellow-200 bg-yellow-100 text-yellow-700 shadow-[inset_0_0_0_1px_rgba(234,179,8,0.06)]",
  low: "border-slate-200 bg-slate-100 text-slate-700 shadow-[inset_0_0_0_1px_rgba(100,116,139,0.05)]",
};

export default function PriorityBadge({ value }: PriorityBadgeProps) {
  const tone = getPriorityTone(value);
  return (
    <span
      className={`inline-flex min-w-[78px] items-center justify-center rounded-full border px-3 py-1.5 text-xs font-semibold ${toneClasses[tone]}`}
    >
      {formatPriority(value)}
    </span>
  );
}
