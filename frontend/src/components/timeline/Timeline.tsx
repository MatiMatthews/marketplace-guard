import { buildTimeline } from "../../lib/mappers";
import type { AlertDetailResponse } from "../../types/api";
import Panel from "../layout/Panel";
import TimelineItem from "./TimelineItem";

type TimelineProps = {
  detail: AlertDetailResponse | null;
};

export default function Timeline({ detail }: TimelineProps) {
  const events = detail ? buildTimeline(detail) : [];

  return (
    <Panel title="Timeline" subtitle="Eventos de la alerta">
      {!detail ? (
        <p className="text-sm text-muted">Sin alerta seleccionada.</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-muted">No hay eventos todavía.</p>
      ) : (
        <div className="space-y-3.5">
          {events.map((event, index) => (
            <TimelineItem event={event} key={`${event.event_type}-${event.timestamp}-${index}`} />
          ))}
        </div>
      )}
    </Panel>
  );
}
