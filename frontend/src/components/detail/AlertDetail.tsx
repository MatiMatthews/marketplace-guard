import { formatDateTime } from "../../lib/format";
import { getAlertTypeLabel, getChannelLabel, getListingLabel } from "../../lib/mappers";
import type { AlertDetailResponse } from "../../types/api";
import EmptyState from "../common/EmptyState";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";
import Panel from "../layout/Panel";
import ExplanationBlock from "./ExplanationBlock";
import PricingSummary from "./PricingSummary";
import PriorityBreakdown from "./PriorityBreakdown";

type AlertDetailProps = {
  detail: AlertDetailResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className="inline-flex rounded-full border border-slate-200 bg-slate-100 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-700">
      {status}
    </span>
  );
}

export default function AlertDetail({
  detail,
  loading,
  error,
  onRetry,
}: AlertDetailProps) {
  return (
    <Panel title="Alert Detail" subtitle="Contexto económico y explicación" className="h-full">
      {loading ? <LoadingState label="Cargando detalle..." /> : null}
      {!loading && error ? <ErrorState message={error} onRetry={onRetry} /> : null}
      {!loading && !error && !detail ? (
        <EmptyState
          title="Selecciona una alerta"
          description="El detalle aparece acá con pricing, explicación y score."
        />
      ) : null}

      {!loading && !error && detail ? (
        <div className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-2xl font-semibold tracking-[-0.03em] text-slate-950">{detail.alert.sku}</p>
                <p className="mt-1.5 text-sm text-slate-500">{detail.alert.product_name}</p>
              </div>
              <StatusBadge status={detail.alert.status} />
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <p className="metric-label">Canal / publicación</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">
                  {getChannelLabel(detail.alert)} / {getListingLabel(detail)}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <p className="metric-label">Tipo</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">
                  {getAlertTypeLabel(detail.alert.alert_type)}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <p className="metric-label">Creada</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">
                  {formatDateTime(detail.alert.created_at)}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <p className="metric-label">Actualizada</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">
                  {formatDateTime(detail.alert.updated_at)}
                </p>
              </div>
            </div>
          </div>

          <PricingSummary detail={detail} />
          <PriorityBreakdown alert={detail.alert} />
          <ExplanationBlock
            explanation={detail.alert.explanation}
            title={detail.alert.title}
          />
        </div>
      ) : null}
    </Panel>
  );
}
