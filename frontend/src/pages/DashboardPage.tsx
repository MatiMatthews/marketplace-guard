import { useEffect, useState } from "react";
import { DEFAULT_REQUESTED_BY } from "../app/config";
import ActionPanel from "../components/actions/ActionPanel";
import AlertDetail from "../components/detail/AlertDetail";
import AlertInbox from "../components/inbox/AlertInbox";
import DashboardShell from "../components/layout/DashboardShell";
import Timeline from "../components/timeline/Timeline";
import { useAlertDetail } from "../hooks/useAlertDetail";
import { useAlerts } from "../hooks/useAlerts";

export default function DashboardPage() {
  const {
    alerts,
    loading: alertsLoading,
    error: alertsError,
    refresh: refreshAlerts,
    loadDemoData,
    isSeeding,
  } = useAlerts(DEFAULT_REQUESTED_BY);
  const [selectedAlertId, setSelectedAlertId] = useState<number | null>(null);
  const {
    detail,
    loading: detailLoading,
    error: detailError,
    refresh: refreshDetail,
  } = useAlertDetail(selectedAlertId);

  useEffect(() => {
    if (alerts.length === 0) {
      setSelectedAlertId(null);
      return;
    }

    const hasCurrentSelection = alerts.some((item) => item.id === selectedAlertId);
    if (!hasCurrentSelection) {
      setSelectedAlertId(alerts[0].id);
    }
  }, [alerts, selectedAlertId]);

  async function handleActionCompleted() {
    await refreshAlerts();
    await refreshDetail();
  }

  return (
    <div className="min-h-screen bg-bg px-4 py-6 text-ink lg:px-6 lg:py-8">
      <div className="mx-auto max-w-[1600px]">
        <div className="section-card mb-6 overflow-hidden rounded-[30px] border border-slate-200/80 bg-[linear-gradient(135deg,#ffffff_0%,#f7f9fc_58%,#eef3f8_100%)] px-6 py-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="max-w-3xl">
              <p className="panel-title">Marketplace Guard</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-slate-950 lg:text-[2rem]">
                Cockpit operativo de alertas
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
                Visibilidad rápida de margen roto, inconsistencias de precio y acciones
                sugeridas para marketplaces.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-sm">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                Operación
              </p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                Inbox, detalle y acción en una sola vista
              </p>
            </div>
          </div>
        </div>

        <DashboardShell
          center={
            <AlertDetail
              detail={detail}
              error={detailError}
              loading={detailLoading}
              onRetry={() => void refreshDetail()}
            />
          }
          left={
            <AlertInbox
              alerts={alerts}
              error={alertsError}
              isSeeding={isSeeding}
              loading={alertsLoading}
              onLoadDemo={() => void loadDemoData()}
              onRetry={() => void refreshAlerts()}
              onSelect={setSelectedAlertId}
              selectedAlertId={selectedAlertId}
            />
          }
          right={
            <div className="space-y-4">
              <ActionPanel
                detail={detail}
                onCompleted={handleActionCompleted}
                requestedBy={DEFAULT_REQUESTED_BY}
              />
              <Timeline detail={detail} />
            </div>
          }
        />
      </div>
    </div>
  );
}
