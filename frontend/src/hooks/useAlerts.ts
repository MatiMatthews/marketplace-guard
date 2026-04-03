import { useEffect, useState } from "react";
import { getAlerts, simulateRun } from "../lib/api";
import { sortAlertsByPriority } from "../lib/mappers";
import type { AlertRecord } from "../types/api";

export function useAlerts(requestedBy: string) {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSeeding, setIsSeeding] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const nextAlerts = await getAlerts();
      setAlerts(sortAlertsByPriority(nextAlerts));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron cargar las alertas.");
    } finally {
      setLoading(false);
    }
  }

  async function loadDemoData() {
    setIsSeeding(true);
    setError(null);
    try {
      await simulateRun(requestedBy);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar la demo.");
    } finally {
      setIsSeeding(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return {
    alerts,
    loading,
    error,
    refresh,
    loadDemoData,
    isSeeding,
  };
}
