import type { AlertRecord } from "../../types/api";
import EmptyState from "../common/EmptyState";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";
import Panel from "../layout/Panel";
import AlertInboxItem from "./AlertInboxItem";

type AlertInboxProps = {
  alerts: AlertRecord[];
  selectedAlertId: number | null;
  onSelect: (alertId: number) => void;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onLoadDemo: () => void;
  isSeeding: boolean;
};

export default function AlertInbox({
  alerts,
  selectedAlertId,
  onSelect,
  loading,
  error,
  onRetry,
  onLoadDemo,
  isSeeding,
}: AlertInboxProps) {
  return (
    <Panel
      title="Alert Inbox"
      subtitle="Ordenada por priority_score"
      className="h-full"
      actions={
        <button
          className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSeeding}
          onClick={onLoadDemo}
          type="button"
        >
          {isSeeding ? "Cargando demo..." : "Cargar demo"}
        </button>
      }
    >
      {loading ? <LoadingState label="Cargando alertas..." /> : null}
      {!loading && error ? <ErrorState message={error} onRetry={onRetry} /> : null}
      {!loading && !error && alerts.length === 0 ? (
        <EmptyState
          title="No hay alertas todavía"
          description="El backend está arriba, pero todavía no generó alertas. Carga una demo para poblar la inbox."
          actionLabel="Generar alertas demo"
          onAction={onLoadDemo}
          loading={isSeeding}
        />
      ) : null}

      {!loading && !error && alerts.length > 0 ? (
        <div className="space-y-2.5">
          {alerts.map((alert) => (
            <AlertInboxItem
              alert={alert}
              key={alert.id}
              onSelect={onSelect}
              selected={selectedAlertId === alert.id}
            />
          ))}
        </div>
      ) : null}
    </Panel>
  );
}
