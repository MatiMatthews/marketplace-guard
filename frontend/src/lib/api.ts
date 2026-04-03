import { API_BASE_URL } from "../app/config";
import type {
  AlertActionRequest,
  AlertActionResponse,
  AlertDetailResponse,
  AlertRecord,
  ApiEnvelope,
} from "../types/api";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof (payload as { detail?: unknown }).detail === "string"
        ? String((payload as { detail?: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export async function getAlerts() {
  const payload = await request<ApiEnvelope<AlertRecord[]>>("/alerts");
  return payload.data;
}

export async function getAlertDetail(alertId: number) {
  const payload = await request<ApiEnvelope<AlertDetailResponse>>(`/alerts/${alertId}`);
  return payload.data;
}

export async function runAlertAction(alertId: number, body: AlertActionRequest) {
  const payload = await request<ApiEnvelope<AlertActionResponse>>(
    `/alerts/${alertId}/actions`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
  return payload.data;
}

export async function simulateRun(requestedBy: string) {
  const payload = await request<ApiEnvelope<unknown>>("/simulate-run", {
    method: "POST",
    body: JSON.stringify({
      requested_by: requestedBy,
    }),
  });
  return payload.data;
}
