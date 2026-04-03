import { formatDateTime } from "../../lib/format";
import type { TimelineEvent } from "../../types/api";

type TimelineItemProps = {
  event: TimelineEvent;
};

export default function TimelineItem({ event }: TimelineItemProps) {
  return (
    <div className="relative pl-7">
      <span className="absolute left-0 top-2.5 h-2.5 w-2.5 rounded-full bg-slate-900 ring-4 ring-slate-100" />
      <span className="absolute left-[4px] top-6 h-[calc(100%-10px)] w-px bg-slate-200" />
      <div className="rounded-xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-3.5 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-semibold text-slate-950">{event.title}</p>
          <span className="text-xs font-medium text-slate-500">{formatDateTime(event.timestamp)}</span>
        </div>
        {Object.keys(event.details).length > 0 ? (
          <div className="mt-2.5 space-y-1.5 text-xs text-slate-500">
            {Object.entries(event.details).map(([key, value]) => (
              <p key={key}>
                <span className="font-semibold text-slate-700">{key}:</span>{" "}
                {typeof value === "string" || typeof value === "number"
                  ? String(value)
                  : JSON.stringify(value)}
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
