import { useEffect, useState } from "react";
import { getAlertDetail } from "../lib/api";
import type { AlertDetailResponse } from "../types/api";

export function useAlertDetail(alertId: number | null) {
  const [detail, setDetail] = useState<AlertDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (alertId === null) {
      setDetail(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const nextDetail = await getAlertDetail(alertId);
      setDetail(nextDetail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el detalle.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, [alertId]);

  return {
    detail,
    loading,
    error,
    refresh,
  };
}
